from datetime import date, datetime, timedelta

from fastapi import APIRouter

from app.config import CIRCUITS, DRIVERS, TEAMS, CURRENT_SEASON
from app.data.loader import load
from app.data.event_roster import resolve_roster

router = APIRouter()


def _parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _circuit(circuit_id):
    return next((c for c in CIRCUITS if c["id"] == circuit_id), None)


def _driver(driver_id):
    return next((d for d in DRIVERS if d["id"] == driver_id), None)


def _team(team_id):
    return next((t for t in TEAMS if t["id"] == team_id), None)


def _resolve_event(season):
    """Shared by /next and the /{season}/{round}/... endpoints below —
    finds the calendar entry for a round, or the current/next one."""
    calendar = load("race_calendar.json") or {}
    events = calendar.get(str(season), [])
    return events, calendar.get("source", "seed")


@router.get("/next")
def next_race(season: int = CURRENT_SEASON):
    events, source = _resolve_event(season)
    if not events:
        return {"error": "no calendar data for this season — run the pipeline or check data/seed/race_calendar.json"}

    today = date.today()
    events_sorted = sorted(events, key=lambda e: e["round"])
    chosen, status = None, None
    for ev in events_sorted:
        race_date = _parse_date(ev["race_date"])
        if race_date >= today - timedelta(days=3):
            chosen = ev
            status = "race_weekend" if abs((race_date - today).days) <= 3 else "upcoming"
            break
    if chosen is None:
        chosen, status = events_sorted[-1], "season_complete"

    return {
        "season": season, "round": chosen["round"], "event_name": chosen.get("event_name"),
        "circuit": _circuit(chosen["circuit_id"]), "race_date": chosen["race_date"],
        "format": chosen.get("format", "conventional"), "status": status,
        "source": source,
    }


@router.get("/{season}/{round_no}/roster")
def race_roster(season: int, round_no: int):
    events, _ = _resolve_event(season)
    ev = next((e for e in events if e["round"] == round_no), None)
    circuit_id = ev["circuit_id"] if ev else None
    roster = resolve_roster(season, round_no, circuit_id)

    out = []
    for team_id, info in roster.items():
        team = _team(team_id)
        if not team:
            continue
        out.append({
            "team": team,
            "drivers": [_driver(did) for did in info["drivers"] if _driver(did)],
            "source": info["source"],  # "real" | "override" | "default"
        })
    return {"season": season, "round": round_no, "circuit_id": circuit_id, "teams": out}


@router.get("/{season}/{round_no}/predictions")
def race_predictions(season: int, round_no: int):
    """Podium top-5 + a 'Pulse Pick' + a chaos index — built entirely from
    the existing real compatibility model and driver clusters, weighted by
    who's ACTUALLY racing this weekend (resolve_roster), so a driver swap
    changes the prediction correctly with no special-casing here."""
    events, _ = _resolve_event(season)
    ev = next((e for e in events if e["round"] == round_no), None)
    if not ev:
        return {"error": "round not found in calendar"}
    circuit_id = ev["circuit_id"]

    roster = resolve_roster(season, round_no, circuit_id)
    active_driver_ids = [did for info in roster.values() for did in info["drivers"]]

    compat = load("compatibility_predictions.json") or {}
    clusters = load("driver_clusters.json") or {"assignments": {}}
    season_kpis = load("season_kpis.json") or {}
    consistency = season_kpis.get(str(season), {}).get("consistency", {})

    scored = []
    for did in active_driver_ids:
        driver_compat = compat.get(did, {}).get(circuit_id)
        score = driver_compat["score"] if isinstance(driver_compat, dict) else None
        if score is None:
            continue
        cons = consistency.get(did)
        cons_median = cons["median"] if isinstance(cons, dict) else None
        scored.append({
            "driver_id": did, "driver": _driver(did), "score": score,
            "predicted_delta_s": driver_compat.get("predicted_delta_s"),
            "consistency_median_finish": cons_median,
            "style_cluster": clusters["assignments"].get(did, "unknown"),
        })

    if not scored:
        return {
            "season": season, "round": round_no, "circuit_id": circuit_id,
            "error": "no compatibility data resolvable for this weekend's roster yet",
        }

    scored.sort(key=lambda r: -r["score"])
    podium = scored[:3]
    top5 = scored[:5]

    # "Pulse Pick" — best score among drivers who AREN'T already a top-3
    # compatibility favorite by a wide margin, i.e. a plausible form/track
    # standout rather than just repeating the podium call.
    pick_pool = scored[3:8] or scored
    pulse_pick = max(pick_pool, key=lambda r: r["score"])

    # Chaos index: purely a function of how tightly bunched the top scores
    # are — closer scores = harder to call = more likely to be shaken up.
    # Simple, explainable, not a trained model; label reflects that.
    top_scores = [r["score"] for r in scored[:8]]
    spread = (max(top_scores) - min(top_scores)) if len(top_scores) > 1 else 0
    chaos_index = max(0, min(100, round(100 - spread * 2)))

    return {
        "season": season, "round": round_no, "circuit_id": circuit_id,
        "event_name": ev.get("event_name"), "race_date": ev.get("race_date"),
        "podium": podium, "top5": top5, "pulse_pick": pulse_pick,
        "chaos_index": chaos_index,
        "chaos_index_basis": "heuristic — spread of compatibility scores among the top 8, not a trained model",
        "source": "real (compatibility model + driver clusters)",
    }


@router.get("/{season}/{round_no}/actual")
def race_actual(season: int, round_no: int):
    """Real result once the round has happened, joined against the
    prediction this endpoint's sibling produced, with a simple accuracy
    score. Returns 'not_yet_run' before that."""
    race_results = load("race_results.json") or {}
    round_data = race_results.get(str(season), {}).get(str(round_no))
    if not round_data or not round_data.get("race"):
        return {"season": season, "round": round_no, "status": "not_yet_run"}

    prediction = race_predictions(season, round_no)
    actual_podium_ids = [
        e["driver"] for e in sorted(round_data["race"], key=lambda r: (r["position"] is None, r["position"]))[:3]
    ]

    predicted_podium_ids = [r["driver_id"] for r in prediction.get("podium", [])] if "podium" in prediction else []
    hits = len(set(actual_podium_ids) & set(predicted_podium_ids))

    return {
        "season": season, "round": round_no, "status": "complete",
        "actual_podium": [_driver(d) for d in actual_podium_ids],
        "predicted_podium": [_driver(d) for d in predicted_podium_ids],
        "podium_hits": hits, "podium_accuracy_pct": round(hits / 3 * 100, 1),
        "source": "real",
    }
