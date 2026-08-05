"""
Driver style clustering.

Builds a per-driver feature vector from the KPIs computed by the pipeline
(race pace delta, tyre degradation slope, qualifying-vs-race delta,
consistency spread) averaged across seasons with data, standardizes it,
and runs KMeans to group drivers into driving-style clusters. These
clusters feed the compatibility engine's trait vectors on the frontend.

If a driver has no usable history (rookie, or pre-debut), they're left
out of the fit and assigned to their team's cluster centroid instead —
see `assign_fallback_cluster`.
"""
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

CLUSTER_LABELS = {
    0: "Smooth & Consistent",
    1: "Aggressive Attacker",
    2: "Technical Precision",
    3: "Raw Pace / High Variance",
}


def _driver_feature_vector(driver_id, all_seasons):
    """Average a driver's KPIs across every season where data is not 'unknown'."""
    pace_vals, deg_vals, qr_vals, spread_vals = [], [], [], []
    for season, kpis in all_seasons.items():
        pace = kpis.get("race_pace", {}).get(driver_id)
        if isinstance(pace, (int, float)):
            pace_vals.append(pace)
        deg = kpis.get("tyre_degradation", {}).get(driver_id)
        if isinstance(deg, dict) and deg:
            deg_vals.append(np.mean(list(deg.values())))
        qr = kpis.get("quali_race_delta", {}).get(driver_id)
        if isinstance(qr, (int, float)):
            qr_vals.append(qr)
        cons = kpis.get("consistency", {}).get(driver_id)
        if isinstance(cons, dict):
            spread_vals.append(cons["q3"] - cons["q1"])

    if not pace_vals and not deg_vals and not qr_vals and not spread_vals:
        return None

    return [
        np.mean(pace_vals) if pace_vals else 0.0,
        np.mean(deg_vals) if deg_vals else 0.0,
        np.mean(qr_vals) if qr_vals else 0.0,
        np.mean(spread_vals) if spread_vals else 0.0,
    ]


def cluster_driver_styles(all_seasons, drivers, k=4):
    ids, vectors = [], []
    for d in drivers:
        vec = _driver_feature_vector(d["id"], all_seasons)
        if vec is not None:
            ids.append(d["id"])
            vectors.append(vec)

    result = {"labels": CLUSTER_LABELS, "assignments": {}, "centroids": {}}

    if len(vectors) < k:
        for d in drivers:
            result["assignments"][d["id"]] = "unknown"
        return result

    X = np.array(vectors)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(Xs)

    for driver_id, cluster_id in zip(ids, labels):
        result["assignments"][driver_id] = int(cluster_id)

    for cluster_id in range(k):
        result["centroids"][cluster_id] = km.cluster_centers_[cluster_id].tolist()

    fitted_ids = set(ids)
    for d in drivers:
        if d["id"] not in fitted_ids:
            result["assignments"][d["id"]] = "unknown"

    return result
