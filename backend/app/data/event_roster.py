from app.config import TEAMS, EVENT_ROSTER_OVERRIDES
from app.data.loader import load


def resolve_roster(season, round_no, circuit_id):
    """Returns {team_id: {"drivers": [driver_id, ...], "source": "real"|"override"|"default"}}"""
    race_results = load("race_results.json") or {}
    round_data = race_results.get(str(season), {}).get(str(round_no))

    if round_data and round_data.get("race"):
        by_team = {}
        for entry in round_data["race"]:
            team_id = entry.get("team")
            if not team_id:
                continue
            by_team.setdefault(team_id, []).append(entry["driver"])
        if by_team:
            return {tid: {"drivers": drivers, "source": "real"} for tid, drivers in by_team.items()}

    override_key = f"{season}-{circuit_id}"
    override = EVENT_ROSTER_OVERRIDES.get(override_key, {})

    out = {}
    for t in TEAMS:
        drivers = override.get(t["id"], t["drivers"])
        source = "override" if t["id"] in override else "default"
        out[t["id"]] = {"drivers": drivers, "source": source}
    return out


def driver_team_for_event(driver_id, season, round_no, circuit_id):
    """Which team a given driver is racing for this specific weekend."""
    roster = resolve_roster(season, round_no, circuit_id)
    for team_id, info in roster.items():
        if driver_id in info["drivers"]:
            return team_id
    return None
