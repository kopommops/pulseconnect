from fastapi import APIRouter
from app.config import DRIVERS, CIRCUITS, SEASONS
from app.data.loader import load

router = APIRouter()

@router.get("")
def list_drivers():
    traits = load("driver_traits.json") or {}
    clusters = load("driver_clusters.json") or {"assignments": {}}
    out = []
    for d in DRIVERS:
        out.append({
            **d,
            "traits": traits.get(d["id"], "unknown"),
            "style_cluster": clusters["assignments"].get(d["id"], "unknown"),
        })
    return {"drivers": out}

@router.get("/{driver_id}")
def get_driver(driver_id: str):
    d = next((x for x in DRIVERS if x["id"] == driver_id.upper()), None)
    if not d:
        return {"error": "not found"}
    traits = load("driver_traits.json") or {}
    clusters = load("driver_clusters.json") or {"assignments": {}}
    return {**d, "traits": traits.get(d["id"], "unknown"),
            "style_cluster": clusters["assignments"].get(d["id"], "unknown")}

@router.get("/{driver_id}/insights")
def get_driver_insights(driver_id: str):
    """
    Aggregated "profile page" stats: best-predicted circuit, most recent
    season with real consistency data, and average tyre degradation across
    every season that has data. Built from the same generated/seed JSON
    the other endpoints use — no separate computation, just a different view.
    """
    did = driver_id.upper()
    d = next((x for x in DRIVERS if x["id"] == did), None)
    if not d:
        return {"error": "not found"}

    predictions = load("compatibility_predictions.json") or {}
    driver_predictions = predictions.get(did, {})
    best_circuit_id, best_score = None, -1
    for circuit_id, val in driver_predictions.items():
        if isinstance(val, dict) and val.get("score", -1) > best_score:
            best_circuit_id, best_score = circuit_id, val["score"]
    best_circuit = next((c for c in CIRCUITS if c["id"] == best_circuit_id), None)

    season_kpis = load("season_kpis.json") or {}
    latest_consistency, latest_season, tyre_samples = "unknown", None, []
    for season in sorted(SEASONS, reverse=True):
        season_data = season_kpis.get(str(season), {})
        cons = season_data.get("consistency", {}).get(did)
        if cons != "unknown" and cons is not None and latest_consistency == "unknown":
            latest_consistency, latest_season = cons, season
        deg = season_data.get("tyre_degradation", {}).get(did)
        if isinstance(deg, dict):
            tyre_samples.append(deg)

    avg_tyre_deg = "unknown"
    if tyre_samples:
        compounds = set()
        for s in tyre_samples:
            compounds.update(s.keys())
        avg_tyre_deg = {
            c: round(sum(s.get(c, 0) for s in tyre_samples if c in s) / max(1, sum(1 for s in tyre_samples if c in s)), 4)
            for c in compounds
        }

    return {
        "driver_id": did,
        "best_track": {"circuit": best_circuit, "score": best_score} if best_circuit else "unknown",
        "latest_consistency": latest_consistency,
        "latest_consistency_season": latest_season,
        "avg_tyre_degradation": avg_tyre_deg,
    }
