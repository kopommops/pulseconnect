"""
Builds feature rows per (season, round, driver) for the race-outcome
model. Used by BOTH build_race_outcome_model.py (training) and
app/ml/race_outcome.py (live prediction) — imported by both, never
duplicated, so a prediction's features can't silently drift from what
the model was trained on.

Two entry points:
  - build_training_rows(): every real (season, round, driver) row with a
    known result, each computed from strictly-prior history only.
  - build_live_features(season, round, roster): features for an upcoming
    round that has NO result yet, for whichever drivers/teams are
    actually entered this weekend (from event_roster.py) — computed from
    all real history strictly before that round.

Known, documented limitation: `tyre_degradation_avg` reads that row's own
season_kpis.json, a season-long aggregate — for an early round in a
season this technically includes a sliver of same-season future data.
Rebuilding it as a fully rolling per-round metric is future work.

FEATURE_COLUMNS defines the exact order the model is trained AND served
with — do not reorder without retraining.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import GENERATED_DIR, DRIVERS, MIN_RACES_FOR_PREDICTION, RECENT_FORM_WINDOW

FEATURE_COLUMNS = [
    "driver_age",
    "recent_form_points",
    "recent_form_avg_finish",
    "recent_avg_quali_position",
    "recent_quali_known",
    "reliability_rate",
    "circuit_history_avg_finish",
    "circuit_history_known",
    "constructor_recent_points",
    "pit_stop_efficiency_s",
    "pit_stop_efficiency_known",
    "safety_car_rate",
    "safety_car_rate_known",
    "tyre_degradation_avg",
    "tyre_degradation_known",
]
GRID_FEATURE_COLUMNS = FEATURE_COLUMNS + ["grid_position", "grid_position_known"]

DRIVER_BIRTH_DATES = {d["id"]: d["birth_date"] for d in DRIVERS}
FINISHED_STATUSES = {"Finished"}


def _load(filename):
    path = os.path.join(GENERATED_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _is_classified(status):
    return bool(status) and (status in FINISHED_STATUSES or status.startswith("+"))


def _age_at(birth_date_str, race_date_str):
    if not birth_date_str or not race_date_str:
        return None
    b = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    r = datetime.strptime(race_date_str, "%Y-%m-%d").date()
    return r.year - b.year - ((r.month, r.day) < (b.month, b.day))


class _HistoryAccumulator:
    """Walks rounds in chronological order, building up the per-driver /
    per-team / per-circuit history a feature row needs — strictly causal:
    a round's own result is only folded in AFTER that round's row(s) are
    computed, never before."""

    def __init__(self):
        self.driver_history = {}       # driver_id -> [{season, round, position, points, status}, ...]
        self.team_points_history = {}  # team_id -> [(season, round, points), ...]
        self.circuit_history = {}      # (driver_id, circuit_id) -> [position, ...]
        self.team_pit_history = {}     # team_id -> [duration_s, ...]

    def features_for(self, driver_id, team_id, circuit_id, race_date, season_kpis_for_season, circuit_sc_data):
        prior = self.driver_history.get(driver_id, [])
        if len(prior) < MIN_RACES_FOR_PREDICTION:
            return None  # cold start — caller returns "unknown"

        age = _age_at(DRIVER_BIRTH_DATES.get(driver_id), race_date)
        if age is None:
            return None

        recent = prior[-RECENT_FORM_WINDOW:]
        recent_points = sum(r["points"] for r in recent)
        recent_positions = [r["position"] for r in recent if r["position"] is not None]
        recent_avg_finish = (sum(recent_positions) / len(recent_positions)) if recent_positions else 20.0

        recent_quali_positions = [r.get("quali_position") for r in recent if r.get("quali_position") is not None]
        recent_quali_known = len(recent_quali_positions) > 0
        recent_avg_quali_position = (sum(recent_quali_positions) / len(recent_quali_positions)) if recent_quali_positions else 20.0

        reliab_window = prior[-10:]
        reliability_rate = sum(1 for r in reliab_window if _is_classified(r["status"])) / len(reliab_window)

        ch = self.circuit_history.get((driver_id, circuit_id), [])
        circuit_history_known = len(ch) > 0
        circuit_history_avg_finish = (sum(ch) / len(ch)) if ch else 20.0

        team_points = self.team_points_history.get(team_id, [])
        constructor_recent_points = sum(p for (_, _, p) in team_points[-RECENT_FORM_WINDOW * 2:])

        pit_hist = self.team_pit_history.get(team_id, [])
        pit_stop_efficiency_known = len(pit_hist) > 0
        pit_stop_efficiency_s = (sum(pit_hist) / len(pit_hist)) if pit_hist else 23.0

        safety_car_rate_known = bool(circuit_sc_data and circuit_sc_data.get("total_laps"))
        safety_car_rate = (
            (circuit_sc_data["sc_laps"] + circuit_sc_data["vsc_laps"]) / circuit_sc_data["total_laps"]
            if safety_car_rate_known else 0.15
        )

        tyre_deg = (season_kpis_for_season or {}).get("tyre_degradation", {}).get(driver_id)
        tyre_degradation_known = isinstance(tyre_deg, dict) and len(tyre_deg) > 0
        tyre_degradation_avg = (sum(tyre_deg.values()) / len(tyre_deg)) if tyre_degradation_known else 0.05

        feats = {
            "driver_age": age,
            "recent_form_points": recent_points,
            "recent_form_avg_finish": recent_avg_finish,
            "recent_avg_quali_position": recent_avg_quali_position,
            "recent_quali_known": 1.0 if recent_quali_known else 0.0,
            "reliability_rate": reliability_rate,
            "circuit_history_avg_finish": circuit_history_avg_finish,
            "circuit_history_known": 1.0 if circuit_history_known else 0.0,
            "constructor_recent_points": constructor_recent_points,
            "pit_stop_efficiency_s": pit_stop_efficiency_s,
            "pit_stop_efficiency_known": 1.0 if pit_stop_efficiency_known else 0.0,
            "safety_car_rate": safety_car_rate,
            "safety_car_rate_known": 1.0 if safety_car_rate_known else 0.0,
            "tyre_degradation_avg": tyre_degradation_avg,
            "tyre_degradation_known": 1.0 if tyre_degradation_known else 0.0,
        }
        return feats

    def absorb_round(self, season, rnd, race_entries, pit_stop_entries, quali_entries=None):
        quali_lookup = {q["driver"]: q["position"] for q in (quali_entries or [])}
        for entry in race_entries:
            did, team_id = entry["driver"], entry.get("team")
            self.driver_history.setdefault(did, []).append({
                "season": season, "round": rnd, "position": entry.get("position"),
                "points": entry.get("points", 0) or 0, "status": entry.get("status"),
                "quali_position": quali_lookup.get(did),
            })
            if team_id:
                self.team_points_history.setdefault(team_id, []).append((season, rnd, entry.get("points", 0) or 0))
        for stop in pit_stop_entries:
            if stop.get("team"):
                self.team_pit_history.setdefault(stop["team"], []).append(stop["duration_s"])


def _chronological_rounds(race_calendar):
    all_rounds = []
    for season_str, events in race_calendar.items():
        if season_str == "source":
            continue
        for ev in events:
            all_rounds.append((int(season_str), int(ev["round"]), ev["circuit_id"], ev["race_date"]))
    all_rounds.sort(key=lambda r: (r[0], r[1]))
    return all_rounds


def build_training_rows():
    """Every real (season, round, driver) row with a known result."""
    race_results = _load("race_results.json")
    season_kpis = _load("season_kpis.json")
    pit_stops = _load("pit_stops.json")
    track_incidents = _load("track_incidents.json")
    race_calendar = _load("race_calendar.json")

    acc = _HistoryAccumulator()
    rows = []

    for season, rnd, circuit_id, race_date in _chronological_rounds(race_calendar):
        round_data = race_results.get(str(season), {}).get(str(rnd))
        if not round_data or not round_data.get("race"):
            continue
        sc_data = track_incidents.get(str(season), {}).get(str(rnd))
        skpis = season_kpis.get(str(season))

        for entry in round_data["race"]:
            did, team_id, position = entry["driver"], entry.get("team"), entry.get("position")
            feats = acc.features_for(did, team_id, circuit_id, race_date, skpis, sc_data)
            if feats is not None:
                rows.append({
                    "season": season, "round": rnd, "driver": did, "circuit_id": circuit_id, "team": team_id,
                    "podium": 1 if position is not None and position <= 3 else 0,
                    "top5": 1 if position is not None and position <= 5 else 0,
                    "features": feats,
                })

        pit_entries = pit_stops.get(str(season), {}).get(str(rnd), {}).get("stops", [])
        acc.absorb_round(season, rnd, round_data["race"], pit_entries, round_data.get("quali", []))
        for entry in round_data["race"]:
            acc.circuit_history.setdefault((entry["driver"], circuit_id), []).append(
                entry.get("position") if entry.get("position") is not None else 20
            )

    return rows


def build_training_rows_grid_confirmed():
    """Same as build_training_rows(), plus the driver's ACTUAL grid
    position for the round being predicted. Only includes rows where that
    round's real qualifying result exists — pre-2018-ish or otherwise
    unrecorded quali sessions simply don't produce a grid-confirmed row,
    same 'skip rather than fabricate' rule as everywhere else."""
    race_results = _load("race_results.json")
    season_kpis = _load("season_kpis.json")
    pit_stops = _load("pit_stops.json")
    track_incidents = _load("track_incidents.json")
    race_calendar = _load("race_calendar.json")

    acc = _HistoryAccumulator()
    rows = []

    for season, rnd, circuit_id, race_date in _chronological_rounds(race_calendar):
        round_data = race_results.get(str(season), {}).get(str(rnd))
        if not round_data or not round_data.get("race") or not round_data.get("quali"):
            continue
        sc_data = track_incidents.get(str(season), {}).get(str(rnd))
        skpis = season_kpis.get(str(season))
        grid_lookup = {q["driver"]: q["position"] for q in round_data["quali"]}

        for entry in round_data["race"]:
            did, team_id, position = entry["driver"], entry.get("team"), entry.get("position")
            feats = acc.features_for(did, team_id, circuit_id, race_date, skpis, sc_data)
            if feats is not None:
                grid_pos = grid_lookup.get(did)
                feats = {**feats, "grid_position": float(grid_pos) if grid_pos is not None else 20.0,
                          "grid_position_known": 1.0 if grid_pos is not None else 0.0}
                rows.append({
                    "season": season, "round": rnd, "driver": did, "circuit_id": circuit_id, "team": team_id,
                    "podium": 1 if position is not None and position <= 3 else 0,
                    "top5": 1 if position is not None and position <= 5 else 0,
                    "features": feats,
                })

        pit_entries = pit_stops.get(str(season), {}).get(str(rnd), {}).get("stops", [])
        acc.absorb_round(season, rnd, round_data["race"], pit_entries, round_data.get("quali", []))
        for entry in round_data["race"]:
            acc.circuit_history.setdefault((entry["driver"], circuit_id), []).append(
                entry.get("position") if entry.get("position") is not None else 20
            )

    return rows


def build_live_features(season, round_no, roster):
    """Features for an upcoming round with no result yet.
    `roster` = [{"driver": driver_id, "team": team_id}, ...] — this
    weekend's ACTUAL entries, from event_roster.resolve_roster(), so a
    driver swap is reflected automatically with no special-casing here."""
    race_results = _load("race_results.json")
    season_kpis = _load("season_kpis.json")
    pit_stops = _load("pit_stops.json")
    track_incidents = _load("track_incidents.json")
    race_calendar = _load("race_calendar.json")

    calendar_entry = next(
        (ev for ev in race_calendar.get(str(season), []) if int(ev["round"]) == round_no), None
    )
    if calendar_entry is None:
        return {}
    circuit_id, race_date = calendar_entry["circuit_id"], calendar_entry["race_date"]

    acc = _HistoryAccumulator()
    for s, r, cid, _ in _chronological_rounds(race_calendar):
        if (s, r) >= (season, round_no):
            break
        round_data = race_results.get(str(s), {}).get(str(r))
        if not round_data or not round_data.get("race"):
            continue
        pit_entries = pit_stops.get(str(s), {}).get(str(r), {}).get("stops", [])
        acc.absorb_round(s, r, round_data["race"], pit_entries, round_data.get("quali", []))
        for entry in round_data["race"]:
            acc.circuit_history.setdefault((entry["driver"], cid), []).append(
                entry.get("position") if entry.get("position") is not None else 20
            )

    sc_data = track_incidents.get(str(season), {}).get(str(round_no))
    skpis = season_kpis.get(str(season))

    out = {}
    for entry in roster:
        did = entry["driver"]
        feats = acc.features_for(did, entry.get("team"), circuit_id, race_date, skpis, sc_data)
        out[did] = feats  # None means cold start / "unknown"
    return out


def build_live_features_grid_confirmed(season, round_no, roster):
    """Grid-confirmed live features — only usable once qualifying for this
    exact round has actually happened. Returns {} (not per-driver None)
    if that round has no real quali data yet, so the caller can tell
    'not ready yet' apart from 'ready, but this driver is cold-start'."""
    race_results = _load("race_results.json")
    round_data = race_results.get(str(season), {}).get(str(round_no))
    if not round_data or not round_data.get("quali"):
        return {}

    season_kpis = _load("season_kpis.json")
    pit_stops = _load("pit_stops.json")
    track_incidents = _load("track_incidents.json")
    race_calendar = _load("race_calendar.json")

    calendar_entry = next(
        (ev for ev in race_calendar.get(str(season), []) if int(ev["round"]) == round_no), None
    )
    if calendar_entry is None:
        return {}
    circuit_id, race_date = calendar_entry["circuit_id"], calendar_entry["race_date"]

    acc = _HistoryAccumulator()
    for s, r, cid, _ in _chronological_rounds(race_calendar):
        if (s, r) >= (season, round_no):
            break
        rd = race_results.get(str(s), {}).get(str(r))
        if not rd or not rd.get("race"):
            continue
        pit_entries = pit_stops.get(str(s), {}).get(str(r), {}).get("stops", [])
        acc.absorb_round(s, r, rd["race"], pit_entries, rd.get("quali", []))
        for entry in rd["race"]:
            acc.circuit_history.setdefault((entry["driver"], cid), []).append(
                entry.get("position") if entry.get("position") is not None else 20
            )

    sc_data = track_incidents.get(str(season), {}).get(str(round_no))
    skpis = season_kpis.get(str(season))
    grid_lookup = {q["driver"]: q["position"] for q in round_data["quali"]}

    out = {}
    for entry in roster:
        did = entry["driver"]
        feats = acc.features_for(did, entry.get("team"), circuit_id, race_date, skpis, sc_data)
        if feats is not None:
            grid_pos = grid_lookup.get(did)
            feats = {**feats, "grid_position": float(grid_pos) if grid_pos is not None else 20.0,
                      "grid_position_known": 1.0 if grid_pos is not None else 0.0}
        out[did] = feats
    return out


def rows_to_matrix(rows, columns=FEATURE_COLUMNS):
    X = [[r["features"][c] for c in columns] for r in rows]
    y_podium = [r["podium"] for r in rows]
    y_top5 = [r["top5"] for r in rows]
    meta = [{"season": r["season"], "round": r["round"], "driver": r["driver"]} for r in rows]
    return X, y_podium, y_top5, meta