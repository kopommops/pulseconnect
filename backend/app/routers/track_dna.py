import random
from fastapi import APIRouter
from app.config import CIRCUITS, DRIVERS

router = APIRouter()

TRACK_TYPE_DEMAND = {
    "Power":      {"braking": 58, "traction": 55, "apexSpeed": 94, "tyreMgmt": 50, "aero": 35, "technical": 40},
    "Street":     {"braking": 87, "traction": 62, "apexSpeed": 28, "tyreMgmt": 58, "aero": 82, "technical": 93},
    "Technical":  {"braking": 62, "traction": 70, "apexSpeed": 72, "tyreMgmt": 62, "aero": 87, "technical": 86},
    "Balanced":   {"braking": 60, "traction": 68, "apexSpeed": 76, "tyreMgmt": 74, "aero": 78, "technical": 62},
    "High-Speed": {"braking": 64, "traction": 60, "apexSpeed": 91, "tyreMgmt": 64, "aero": 68, "technical": 54},
    "Mixed":      {"braking": 70, "traction": 74, "apexSpeed": 66, "tyreMgmt": 70, "aero": 66, "technical": 70},
}

# Heuristic, not yet pipeline-derived: real tyre wear / pit-stop counts need a
# circuit-keyed extension to build_dataset.py (matching FastF1 event names to
# our circuit ids — see the comment in kpis_from_race_session). Until that
# lands, these are reasonable track-type-based estimates, clearly flagged
# via "source": "heuristic" in the response rather than presented as measured.
TRACK_TYPE_TYRE_WEAR = {
    "Power": "Low", "Street": "Medium", "Technical": "High",
    "Balanced": "Medium", "High-Speed": "Medium", "Mixed": "High",
}
TRACK_TYPE_PIT_STOPS = {
    "Power": 1.3, "Street": 1.8, "Technical": 2.1,
    "Balanced": 2.0, "High-Speed": 1.6, "Mixed": 2.2,
}


@router.get("/{circuit_id}")
def get_track_dna(circuit_id: str):
    c = next((x for x in CIRCUITS if x["id"] == circuit_id), None)
    if not c:
        return {"error": "not found"}
    demand = TRACK_TYPE_DEMAND.get(c["type"], TRACK_TYPE_DEMAND["Balanced"])

    # deterministic "illustrative" best-sector holders (seeded by circuit id
    # so it's stable across requests, not random noise on every call)
    rng = random.Random(circuit_id)
    sector_holders = {
        "s1": rng.choice(DRIVERS)["id"],
        "s2": rng.choice(DRIVERS)["id"],
        "s3": rng.choice(DRIVERS)["id"],
    }

    return {
        **c,
        "demand": demand,
        "tyre_wear_index": TRACK_TYPE_TYRE_WEAR.get(c["type"], "Medium"),
        "avg_pit_stops": TRACK_TYPE_PIT_STOPS.get(c["type"], 2.0),
        "best_sector_holders": sector_holders,
        "source": "heuristic",
    }
