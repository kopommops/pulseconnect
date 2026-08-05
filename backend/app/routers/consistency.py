from fastapi import APIRouter
from app.data.loader import load

router = APIRouter()

@router.get("/{season}")
def get_consistency(season: str):
    data = load("season_kpis.json") or {}
    season_data = data.get(str(season), {})
    return {
        "season": season,
        "consistency": season_data.get("consistency", {}),
        "race_pace": season_data.get("race_pace", {}),
        "quali_race_delta": season_data.get("quali_race_delta", {}),
        "source": season_data.get("source", "generated"),
    }
