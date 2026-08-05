from fastapi import APIRouter
from app.config import CIRCUITS

router = APIRouter()

@router.get("")
def list_circuits():
    return {"circuits": CIRCUITS}

@router.get("/{circuit_id}")
def get_circuit(circuit_id: str):
    c = next((x for x in CIRCUITS if x["id"] == circuit_id), None)
    return c or {"error": "not found"}
