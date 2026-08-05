from fastapi import APIRouter
from app.config import TEAMS

router = APIRouter()

@router.get("")
def list_teams():
    return {"teams": TEAMS}

@router.get("/{team_id}")
def get_team(team_id: str):
    t = next((x for x in TEAMS if x["id"] == team_id), None)
    return t or {"error": "not found"}
