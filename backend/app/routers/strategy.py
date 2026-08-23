from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import CIRCUITS, PIT_LOSS_HEURISTIC_BY_TYPE, CURRENT_SEASON
from app.data.loader import load

router = APIRouter()


class Stint(BaseModel):
    compound: str
    laps: int


class StrategyRequest(BaseModel):
    driver_id: str
    circuit_id: str
    season: int = CURRENT_SEASON
    stints: List[Stint]


@router.post("/{season}/{round_no}/simulate-strategy")
def simulate_strategy(season: int, round_no: int, req: StrategyRequest):
    """Closed-form simulation, not a trained model — real arithmetic on
    real numbers: each stint's time-vs-field is the driver's real per-lap
    pace delta plus the cumulative effect of their real tyre-degradation
    slope for that compound, and each pit stop costs a real-ish (see
    'basis' in the response) circuit pit-loss constant. No new ML needed;
    this is exactly the kind of what-if the existing pipeline output
    already supports."""
    did = req.driver_id.upper()
    circuit = next((c for c in CIRCUITS if c["id"] == req.circuit_id), None)
    if not circuit:
        return {"error": "unknown circuit_id"}

    season_kpis = load("season_kpis.json") or {}
    sdata = season_kpis.get(str(season), {})
    tyre_deg = sdata.get("tyre_degradation", {}).get(did)

    base_pace = sdata.get("race_pace_by_circuit", {}).get(did)
    if isinstance(base_pace, dict):
        base_pace = base_pace.get(req.circuit_id)
    if not isinstance(base_pace, (int, float)):
        base_pace = sdata.get("race_pace", {}).get(did)  # fall back to season-wide pace

    if not isinstance(base_pace, (int, float)) or not isinstance(tyre_deg, dict):
        return {"error": "unknown — insufficient real KPI data for this driver/season to simulate", "driver_id": did}

    pit_loss = PIT_LOSS_HEURISTIC_BY_TYPE.get(circuit["type"], 21.0)
    num_stops = max(0, len(req.stints) - 1)

    total_delta_s = 0.0
    stint_breakdown = []
    for stint in req.stints:
        compound = stint.compound.upper()
        slope = tyre_deg.get(compound)
        known = slope is not None
        slope = slope if known else 0.0
        n = stint.laps
        # Cumulative degradation across the stint relative to its first lap:
        # slope * (0 + 1 + ... + (n-1)) — a standard triangular-number sum.
        cumulative = slope * (n * (n - 1) / 2)
        stint_delta = base_pace * n + cumulative
        total_delta_s += stint_delta
        stint_breakdown.append({
            "compound": compound, "laps": n,
            "degradation_slope_s_per_lap": slope, "degradation_known": known,
            "stint_delta_s": round(stint_delta, 2),
        })

    total_delta_s += pit_loss * num_stops

    return {
        "driver_id": did, "circuit_id": req.circuit_id, "season": season,
        "num_stops": num_stops, "pit_loss_s_per_stop": pit_loss,
        "stints": stint_breakdown,
        "total_predicted_delta_vs_field_s": round(total_delta_s, 2),
        "basis": ("real tyre-degradation slopes + real race-pace baseline from season_kpis.json; "
                   "pit_loss_s is a track-type heuristic (PIT_LOSS_HEURISTIC_BY_TYPE), not yet mined "
                   "from real pit-lane timing — see README known limitations"),
        "source": "real+heuristic",
    }
