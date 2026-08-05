from fastapi import APIRouter
from app.config import DRIVERS
from app.data.loader import load

router = APIRouter()

@router.get("/{driver_a}/{driver_b}")
def compare(driver_a: str, driver_b: str, season: str = "2026"):
    a_id, b_id = driver_a.upper(), driver_b.upper()
    a = next((x for x in DRIVERS if x["id"] == a_id), None)
    b = next((x for x in DRIVERS if x["id"] == b_id), None)
    if not a or not b:
        return {"error": "driver not found"}
    kpis = (load("season_kpis.json") or {}).get(str(season), {})
    traits = load("driver_traits.json") or {}
    return {
        "season": season,
        "driver_a": {**a, "consistency": kpis.get("consistency", {}).get(a_id, "unknown"),
                     "race_pace": kpis.get("race_pace", {}).get(a_id, "unknown"),
                     "traits": traits.get(a_id, "unknown")},
        "driver_b": {**b, "consistency": kpis.get("consistency", {}).get(b_id, "unknown"),
                     "race_pace": kpis.get("race_pace", {}).get(b_id, "unknown"),
                     "traits": traits.get(b_id, "unknown")},
    }
