"""
PulseConnect v2 — dataset build pipeline.

Run this on a machine with normal internet access (FastF1 needs to reach
F1's timing/Ergast data sources, which this sandbox's network does not
permit). It fetches the last 6 seasons, computes every KPI, runs the ML
layer, and writes JSON to backend/data/generated/ — the API serves those
files if present, falling back to data/seed/ otherwise.

v2 fixes a rate-limit bug from the first version: every race was being
loaded up to 5 separate times (once per KPI function), which burns through
FastF1/Jolpica's ~500 calls/hour limit fast. Each race session is now
loaded exactly ONCE (twice if you count qualifying) and every KPI is
derived from that single load. Results are also written incrementally,
per season, so a rate-limit partway through doesn't lose earlier progress
— re-running the script skips seasons that already have a generated file
unless --force is passed.

Race Day update: each round's real per-round result (driver, team,
position, points, status — both quali and race) is now ALSO persisted to
race_results.json, and each season's real event dates to race_calendar.json.
Previously only the season-long KPI aggregate was kept and per-round detail
was discarded; standings, the Race Day predictions-vs-actual comparison,
and the /race-day/next resolver all need that per-round granularity.

Usage:
    cd backend
    pip install -r requirements.txt
    python pipeline/build_dataset.py                # all 6 seasons, skips already-built ones
    python pipeline/build_dataset.py --season 2026   # single season
    python pipeline/build_dataset.py --force         # rebuild everything, ignore existing progress
"""
import argparse
import json
import os
import sys
import time
import warnings

import fastf1
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import SEASONS, CACHE_DIR, GENERATED_DIR, DRIVERS, TEAMS, CIRCUITS, UNKNOWN, circuit_id_for_event
from app.ml.clustering import cluster_driver_styles
from app.ml.predict import fit_compatibility_model, predict_compatibility

warnings.filterwarnings("ignore")

PROGRESS_FILE = os.path.join(GENERATED_DIR, "_progress.json")
MAX_RETRIES = 3
BACKOFF_SECONDS = 90  # FastF1/Jolpica's limit resets on a rolling hourly window;
                       # a short backoff handles transient/burst limiting, a real
                       # hourly ban just fails that season and moves on.

# FastF1's TeamName string varies by season (rebrands, sponsor-name churn —
# e.g. "AlphaTauri" -> "RB" -> "Racing Bulls", "Alfa Romeo"/"Sauber" -> "Audi").
# Best-effort keyword match to our stable internal team_id; unresolved names
# are stored as None rather than guessed, so a stale/new name never silently
# gets misattributed to the wrong constructor.
TEAM_NAME_ALIASES = {
    "redbull": ["red bull"],
    "ferrari": ["ferrari"],
    "mercedes": ["mercedes"],
    "mclaren": ["mclaren"],
    "astonmartin": ["aston martin"],
    "alpine": ["alpine"],
    "racingbulls": ["racing bulls", "alphatauri", "toro rosso"],
    "haas": ["haas"],
    "audi": ["audi", "sauber", "alfa romeo"],
    "williams": ["williams"],
    "cadillac": ["cadillac"],
}


def team_id_from_name(name):
    if not isinstance(name, str):
        return None
    n = name.strip().lower()
    if n == "rb":
        return "racingbulls"
    for team_id, keywords in TEAM_NAME_ALIASES.items():
        if any(k in n for k in keywords):
            return team_id
    return None


def with_retry(fn, *args, label="", **kwargs):
    """Retries a FastF1 call on rate-limit errors with backoff. Any other
    exception is treated as non-recoverable for this call and re-raised."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            is_rate_limit = "rate limit" in str(e).lower() or "500 calls" in str(e).lower()
            if is_rate_limit and attempt < MAX_RETRIES:
                print(f"    ! rate limited on {label}, backing off {BACKOFF_SECONDS}s (attempt {attempt}/{MAX_RETRIES})")
                time.sleep(BACKOFF_SECONDS)
                continue
            raise


def setup_cache():
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)


def driver_has_history(driver, season):
    return season >= driver["debut_season"]


def fetch_season_events(season):
    """Returns [{round, event_name, date, format}], real dates/format from
    FastF1's schedule — this is what race_calendar.json is built from."""
    try:
        schedule = with_retry(fastf1.get_event_schedule, season, label=f"schedule {season}")
        out = []
        for _, r in schedule.iterrows():
            if r.RoundNumber <= 0:
                continue
            date = r.EventDate
            out.append({
                "round": int(r.RoundNumber),
                "event_name": r.EventName,
                "race_date": date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else str(date),
                "format": getattr(r, "EventFormat", "conventional") or "conventional",
            })
        return out
    except Exception as e:
        print(f"  ! could not fetch schedule for {season}: {e}")
        return []


def load_session(season, rnd, kind, **load_kwargs):
    """Load one session exactly once. kind = 'R' or 'Q'."""
    try:
        session = with_retry(fastf1.get_session, season, rnd, kind, label=f"{kind}{rnd}")
        with_retry(session.load, label=f"load {kind}{rnd}", **load_kwargs)

        session.laps
        session.results
        return session
    except Exception as e:
        print(f"    ! {kind} {season} round {rnd} failed: {e}")
        return None


def _blank_accum():
    return {
        "positions": [], "pace_deltas": [], "pace_deltas_by_circuit": {},
        "tyre_slopes": {}, "best_sectors": {}, "quali_race_diffs": [],
    }


def kpis_from_race_session(race, driver_kpis, circuit_id=None):
    """Derive consistency + race-pace + tyre-degradation + best-sector stats
    from a single loaded race session, appending into the running
    per-driver accumulators in `driver_kpis`.

    `circuit_id` (resolved once per round in build_season via
    circuit_id_for_event) tags each driver's pace delta with the circuit it
    was set at, so the compatibility model can later learn a real
    driver-x-circuit relationship instead of a single season-wide average
    repeated across every circuit."""
    if race is None:
        return

    if race.results is not None and not race.results.empty:
        for _, row in race.results.iterrows():
            drv, pos = row.get("Abbreviation"), row.get("Position")
            if drv and not pd.isna(pos):
                driver_kpis.setdefault(drv, _blank_accum())["positions"].append(int(pos))

    laps = race.laps
    if laps is None or laps.empty:
        return

    quicklaps = laps.pick_quicklaps() if hasattr(laps, "pick_quicklaps") else laps
    quicklaps = quicklaps[quicklaps["LapTime"].notna()]
    if not quicklaps.empty:
        field_median = quicklaps["LapTime"].dt.total_seconds().median()
        for drv, grp in quicklaps.groupby("Driver"):
            drv_median = grp["LapTime"].dt.total_seconds().median()
            delta = drv_median - field_median
            acc = driver_kpis.setdefault(drv, _blank_accum())
            acc["pace_deltas"].append(delta)
            if circuit_id:
                acc["pace_deltas_by_circuit"].setdefault(circuit_id, []).append(delta)

    for (drv, stint), grp in laps.groupby(["Driver", "Stint"]):
        grp = grp.sort_values("LapNumber")
        if len(grp) < 5:
            continue
        grp = grp.iloc[1:-1]
        grp = grp[grp["LapTime"].notna()]
        if len(grp) < 3:
            continue
        x = grp["LapNumber"].astype(float).values
        y = grp["LapTime"].dt.total_seconds().values
        slope = float(np.polyfit(x, y, 1)[0])
        compound = grp["Compound"].iloc[0] if "Compound" in grp else "UNKNOWN"
        driver_kpis.setdefault(drv, _blank_accum())["tyre_slopes"].setdefault(compound, []).append(slope)

    for sector_col, key in [("Sector1Time", "s1"), ("Sector2Time", "s2"), ("Sector3Time", "s3")]:
        if sector_col not in laps.columns:
            continue
        valid = laps[laps[sector_col].notna()]
        if valid.empty:
            continue
        best_row = valid.loc[valid[sector_col].idxmin()]
        driver_kpis.setdefault(best_row["Driver"], _blank_accum())["best_sectors"][key] = \
            round(best_row[sector_col].total_seconds(), 3)


def kpis_from_quali_race_pair(quali, race, driver_kpis):
    if quali is None or race is None or quali.results is None or race.results is None:
        return
    qpos = {row["Abbreviation"]: row["Position"] for _, row in quali.results.iterrows()}
    for _, row in race.results.iterrows():
        drv = row.get("Abbreviation")
        if drv in qpos and not pd.isna(qpos[drv]) and not pd.isna(row.get("Position")):
            driver_kpis.setdefault(drv, _blank_accum())["quali_race_diffs"].append(
                float(qpos[drv]) - float(row["Position"]))


def round_result_from_sessions(quali, race, circuit_id):
    """Real per-round result — driver, team (resolved from FastF1's own
    TeamName, so a mid-season or single-weekend driver swap is captured
    correctly with no manual bookkeeping), position, points, status.
    This is the new artifact standings/predictions-vs-actual read from."""
    result = {"circuit_id": circuit_id, "quali": [], "race": [], "source": "real"}

    if quali is not None and quali.results is not None and not quali.results.empty:
        for _, row in quali.results.iterrows():
            drv, pos = row.get("Abbreviation"), row.get("Position")
            if drv and not pd.isna(pos):
                result["quali"].append({"driver": drv, "position": int(pos)})

    if race is not None and race.results is not None and not race.results.empty:
        for _, row in race.results.iterrows():
            drv = row.get("Abbreviation")
            if not drv:
                continue
            pos = row.get("Position")
            points = row.get("Points")
            status = row.get("Status")
            result["race"].append({
                "driver": drv,
                "team": team_id_from_name(row.get("TeamName")),
                "position": int(pos) if not pd.isna(pos) else None,
                "points": float(points) if points is not None and not pd.isna(points) else 0.0,
                "status": status if isinstance(status, str) else "Unknown",
                "fastest_lap": bool(row.get("Position") == 1 and float(points or 0) % 1 != 0) if points is not None else False,
            })

    return result


def finalize_season_kpis(driver_kpis, season):
    consistency, race_pace, race_pace_by_circuit, tyre_deg, quali_race = {}, {}, {}, {}, {}
    for d in DRIVERS:
        did = d["id"]
        acc = driver_kpis.get(did)
        has_hist = driver_has_history(d, season)

        consistency[did] = UNKNOWN
        race_pace[did] = UNKNOWN
        race_pace_by_circuit[did] = UNKNOWN
        tyre_deg[did] = UNKNOWN
        quali_race[did] = UNKNOWN
        if not has_hist or acc is None:
            continue

        if acc["positions"]:
            arr = np.array(acc["positions"])
            consistency[did] = {
                "min": int(arr.min()), "q1": float(np.percentile(arr, 25)),
                "median": float(np.median(arr)), "q3": float(np.percentile(arr, 75)),
                "max": int(arr.max()), "n_races": int(len(arr)),
            }
        if acc["pace_deltas"]:
            race_pace[did] = round(float(np.mean(acc["pace_deltas"])), 3)
        if acc["pace_deltas_by_circuit"]:
            race_pace_by_circuit[did] = {
                cid: round(float(np.mean(vals)), 3)
                for cid, vals in acc["pace_deltas_by_circuit"].items()
            }
        if acc["tyre_slopes"]:
            tyre_deg[did] = {c: round(float(np.mean(v)), 4) for c, v in acc["tyre_slopes"].items()}
        if acc["quali_race_diffs"]:
            quali_race[did] = round(float(np.mean(acc["quali_race_diffs"])), 2)

    return {
        "consistency": consistency, "race_pace": race_pace,
        "race_pace_by_circuit": race_pace_by_circuit,
        "tyre_degradation": tyre_deg, "quali_race_delta": quali_race,
    }


def build_season(season):
    print(f"\n== Season {season} ==")
    events = fetch_season_events(season)
    print(f"  {len(events)} events found")

    driver_kpis = {}
    round_results = {}
    for ev in events:
        rnd, event_name = ev["round"], ev["event_name"]
        circuit_id = circuit_id_for_event(event_name)
        if circuit_id is None:
            print(f"  round {rnd}: {event_name}  ! no circuit_id match — pace won't be tagged per-circuit for this round")
        else:
            print(f"  round {rnd}: {event_name} -> {circuit_id}")
        race = load_session(season, rnd, "R", telemetry=False, weather=False, messages=False)
        kpis_from_race_session(race, driver_kpis, circuit_id=circuit_id)
        quali = load_session(season, rnd, "Q", telemetry=False, weather=False, messages=False)
        kpis_from_quali_race_pair(quali, race, driver_kpis)

        round_result = round_result_from_sessions(quali, race, circuit_id)
        if round_result["race"] or round_result["quali"]:
            round_results[str(rnd)] = round_result

    season_kpis = finalize_season_kpis(driver_kpis, season)
    return season_kpis, round_results, events


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(all_seasons, all_round_results, all_calendars):
    with open(os.path.join(GENERATED_DIR, "season_kpis.json"), "w") as f:
        json.dump(all_seasons, f, indent=2, default=str)
    with open(os.path.join(GENERATED_DIR, "race_results.json"), "w") as f:
        json.dump(all_round_results, f, indent=2, default=str)
    with open(os.path.join(GENERATED_DIR, "race_calendar.json"), "w") as f:
        json.dump({**all_calendars, "source": "real"}, f, indent=2, default=str)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"completed_seasons": list(all_seasons.keys())}, f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", type=int, default=None, help="build a single season instead of all 6")
    parser.add_argument("--force", action="store_true", help="rebuild seasons even if already completed")
    args = parser.parse_args()

    setup_cache()
    os.makedirs(GENERATED_DIR, exist_ok=True)

    progress = load_progress() if not args.force else {}
    already_done = set(progress.get("completed_seasons", []))

    existing, existing_round_results, existing_calendars = {}, {}, {}
    existing_kpis_path = os.path.join(GENERATED_DIR, "season_kpis.json")
    existing_results_path = os.path.join(GENERATED_DIR, "race_results.json")
    existing_calendar_path = os.path.join(GENERATED_DIR, "race_calendar.json")
    if not args.force:
        if os.path.exists(existing_kpis_path):
            with open(existing_kpis_path) as f:
                existing = json.load(f)
        if os.path.exists(existing_results_path):
            with open(existing_results_path) as f:
                existing_round_results = json.load(f)
        if os.path.exists(existing_calendar_path):
            with open(existing_calendar_path) as f:
                existing_calendars = {k: v for k, v in json.load(f).items() if k != "source"}

    seasons_to_build = [args.season] if args.season else SEASONS
    all_seasons = dict(existing)
    all_round_results = dict(existing_round_results)
    all_calendars = dict(existing_calendars)

    for season in seasons_to_build:
        if str(season) in already_done and not args.force:
            print(f"\n== Season {season} == already built, skipping (use --force to rebuild)")
            continue
        season_kpis, round_results, events = build_season(season)
        all_seasons[str(season)] = season_kpis
        all_round_results[str(season)] = round_results
        all_calendars[str(season)] = events
        save_progress(all_seasons, all_round_results, all_calendars)  # save after every season

    print(f"\nWrote {GENERATED_DIR}/season_kpis.json ({len(all_seasons)} seasons)")
    print(f"Wrote {GENERATED_DIR}/race_results.json, {GENERATED_DIR}/race_calendar.json")

    print("\n== ML: clustering driver styles ==")
    clusters = cluster_driver_styles(all_seasons, DRIVERS)
    with open(os.path.join(GENERATED_DIR, "driver_clusters.json"), "w") as f:
        json.dump(clusters, f, indent=2, default=str)
    print(f"Wrote {GENERATED_DIR}/driver_clusters.json")

    print("\n== ML: fitting compatibility model ==")

    model, feature_cols = fit_compatibility_model(all_seasons, DRIVERS, CIRCUITS, clusters)
    predictions = predict_compatibility(model, feature_cols, DRIVERS, CIRCUITS, clusters, all_seasons)
    with open(os.path.join(GENERATED_DIR, "compatibility_predictions.json"), "w") as f:
        json.dump(predictions, f, indent=2, default=str)
    print(f"Wrote {GENERATED_DIR}/compatibility_predictions.json")

    print("\nDone. Restart the API (or it will hot-read on next request) to serve real data.")
    if len(all_seasons) < len(SEASONS):
        missing = set(str(s) for s in SEASONS) - set(all_seasons.keys())
        print(f"Note: {len(missing)} season(s) still missing ({sorted(missing)}) — likely hit the hourly rate")
        print("limit. Just re-run this script later (same command); completed seasons are skipped automatically.")


if __name__ == "__main__":
    main()
