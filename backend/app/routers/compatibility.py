from fastapi import APIRouter
from app.data.loader import load

router = APIRouter()

@router.get("")
def get_all_compatibility():
    return load("compatibility_predictions.json") or {"error": "no data — run pipeline or build_seed"}

@router.get("/{driver_id}/{circuit_id}")
def get_compatibility(driver_id: str, circuit_id: str):
    data = load("compatibility_predictions.json") or {}
    return data.get(driver_id.upper(), {}).get(circuit_id, "unknown")
