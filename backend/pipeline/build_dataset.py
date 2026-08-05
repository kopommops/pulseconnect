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


def fetch_season_races(season):
    try:
        schedule = with_retry(fastf1.get_event_schedule, season, label=f"schedule {season}")
        return [(int(r.RoundNumber), r.EventName) for _, r in schedule.iterrows() if r.RoundNumber > 0]
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
    races = fetch_season_races(season)
    print(f"  {len(races)} events found")

    driver_kpis = {}
    for rnd, event_name in races:
        circuit_id = circuit_id_for_event(event_name)
        if circuit_id is None:
            print(f"  round {rnd}: {event_name}  ! no circuit_id match — pace won't be tagged per-circuit for this round")
        else:
            print(f"  round {rnd}: {event_name} -> {circuit_id}")
        race = load_session(season, rnd, "R", telemetry=False, weather=False, messages=False)
        kpis_from_race_session(race, driver_kpis, circuit_id=circuit_id)
        quali = load_session(season, rnd, "Q", telemetry=False, weather=False, messages=False)
        kpis_from_quali_race_pair(quali, race, driver_kpis)

    return finalize_season_kpis(driver_kpis, season)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(all_seasons):
    with open(os.path.join(GENERATED_DIR, "season_kpis.json"), "w") as f:
        json.dump(all_seasons, f, indent=2, default=str)
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

    existing = {}
    existing_path = os.path.join(GENERATED_DIR, "season_kpis.json")
    if os.path.exists(existing_path) and not args.force:
        with open(existing_path) as f:
            existing = json.load(f)

    seasons_to_build = [args.season] if args.season else SEASONS
    all_seasons = dict(existing)

    for season in seasons_to_build:
        if str(season) in already_done and not args.force:
            print(f"\n== Season {season} == already built, skipping (use --force to rebuild)")
            continue
        all_seasons[str(season)] = build_season(season)
        save_progress(all_seasons)  # save after every season, not just at the end

    print(f"\nWrote {GENERATED_DIR}/season_kpis.json ({len(all_seasons)} seasons)")

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