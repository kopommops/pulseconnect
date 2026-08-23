from fastapi import APIRouter

from app.config import TEAMS, DRIVERS
from app.data.loader import load

router = APIRouter()


def _driver_name(did):
    d = next((x for x in DRIVERS if x["id"] == did), None)
    return d["name"] if d else did


def _team_name(tid):
    t = next((x for x in TEAMS if x["id"] == tid), None)
    return t["name"] if t else tid


@router.get("/{season}")
def get_standings(season: str):
    """Computed on-request from race_results.json — not persisted — so it
    stays correct automatically as new rounds land, no regeneration step."""
    race_results = load("race_results.json") or {}
    season_data = race_results.get(season)
    if not season_data:
        return {"error": "no real per-round results yet for this season — run the pipeline", "season": season}

    driver_points, constructor_points = {}, {}
    driver_wins, driver_podiums = {}, {}
    rounds_counted = 0

    for _, round_data in sorted(season_data.items(), key=lambda kv: int(kv[0])):
        race_entries = round_data.get("race", [])
        if not race_entries:
            continue
        rounds_counted += 1
        for entry in race_entries:
            did, pts, pos, team = entry["driver"], entry.get("points", 0) or 0, entry.get("position"), entry.get("team")
            driver_points[did] = driver_points.get(did, 0) + pts
            if team:
                constructor_points[team] = constructor_points.get(team, 0) + pts
            if pos == 1:
                driver_wins[did] = driver_wins.get(did, 0) + 1
            if pos is not None and pos <= 3:
                driver_podiums[did] = driver_podiums.get(did, 0) + 1

    drivers = sorted([
        {"driver_id": did, "name": _driver_name(did), "points": round(pts, 1),
         "wins": driver_wins.get(did, 0), "podiums": driver_podiums.get(did, 0)}
        for did, pts in driver_points.items()
    ], key=lambda r: (-r["points"], -r["wins"]))
    for i, row in enumerate(drivers, 1):
        row["position"] = i

    constructors = sorted([
        {"team_id": tid, "name": _team_name(tid), "points": round(pts, 1)}
        for tid, pts in constructor_points.items()
    ], key=lambda r: -r["points"])
    for i, row in enumerate(constructors, 1):
        row["position"] = i

    return {
        "season": season, "rounds_counted": rounds_counted,
        "drivers": drivers, "constructors": constructors,
        "source": "real",
    }
