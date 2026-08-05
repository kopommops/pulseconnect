import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

TRACK_TYPES = ["Power", "Street", "Technical", "Balanced", "High-Speed", "Mixed"]
def _driver_circuit_features(driver_id, circuit, all_seasons, clusters):
    # Guard against None
    if all_seasons is None:
        all_seasons = {}
    if clusters is None:
        clusters = {}

    # 1. Circuit Features
    circuit_onehot = [1.0 if circuit.get("type") == t else 0.0 for t in TRACK_TYPES]
    circuit_dims = [circuit.get("length_km", 0.0) / 7.0, circuit.get("corners", 0) / 27.0]
    
    # 2. Driver Features (Averaged KPIs + Cluster ID)
    pace_vals, deg_vals, qr_vals = [], [], []
    for season, kpis in all_seasons.items():
        if not isinstance(kpis, dict):
            continue
            
        pace = kpis.get("race_pace", {}).get(driver_id)
        if isinstance(pace, (int, float)):
            pace_vals.append(pace)
            
        deg = kpis.get("tyre_degradation", {}).get(driver_id)
        if isinstance(deg, dict) and deg:
            deg_vals.append(np.mean(list(deg.values())))
            
        qr = kpis.get("quali_race_delta", {}).get(driver_id)
        if isinstance(qr, (int, float)):
            qr_vals.append(qr)

    mean_pace = float(np.mean(pace_vals)) if pace_vals else 0.0
    mean_deg = float(np.mean(deg_vals)) if deg_vals else 0.0
    mean_qr = float(np.mean(qr_vals)) if qr_vals else 0.0
    
    assignments = clusters.get("assignments", {}) if isinstance(clusters, dict) else {}
    cluster_id = assignments.get(driver_id, -1)
    cluster_feat = [float(cluster_id)] if isinstance(cluster_id, int) else [-1.0]

    return circuit_onehot + circuit_dims + [mean_pace, mean_deg, mean_qr] + cluster_feat

def _training_rows(all_seasons, drivers, circuits, clusters):
    """Build (X, y) with a genuine per-circuit target.

    Each row pairs a driver+circuit's real pace delta *at that circuit that
    season* (race_pace_by_circuit) with that circuit's real features, so the
    circuit-derived part of the feature vector actually correlates with y.

    Previously this paired one season-wide average (race_pace) against every
    circuit indiscriminately, so y never varied with the circuit features and
    the model learned to ignore them — collapsing predictions to a
    driver-only average regardless of which circuit was queried.
    """
    X, y = [], []
    for season, kpis in all_seasons.items():
        by_circuit = kpis.get("race_pace_by_circuit", {})
        for d in drivers:
            driver_id = d["id"] if isinstance(d, dict) else d
            circuit_paces = by_circuit.get(driver_id)
            if not isinstance(circuit_paces, dict):
                continue  # "unknown" (no history) or old-schema data without this field
            for c in circuits:
                circuit_id = c["id"] if isinstance(c, dict) else c
                val = circuit_paces.get(circuit_id)
                if not isinstance(val, (int, float)):
                    continue  # driver never raced at this circuit in this season
                feats = _driver_circuit_features(driver_id, c, all_seasons, clusters)
                X.append(feats)
                y.append(val)
    return np.array(X), np.array(y)

FEATURE_COLS = [
    "type_Power", "type_Street", "type_Technical", "type_Balanced", "type_High-Speed", "type_Mixed",
    "norm_length", "norm_corners",
    "mean_pace", "mean_deg", "mean_qr",
    "cluster_id"
]

def fit_compatibility_model(all_seasons, drivers, circuits, clusters):
    X, y = _training_rows(all_seasons, drivers, circuits, clusters)
    if len(X) < 20:
        return None, FEATURE_COLS
        
    model = GradientBoostingRegressor(
        n_estimators=150, 
        max_depth=4, 
        learning_rate=0.05, 
        random_state=42
    )
    model.fit(X, y)
    
    return model, FEATURE_COLS

def predict_compatibility(model, feature_cols, drivers, circuits, clusters, all_seasons=None):
    out = {}
    assignments = clusters.get("assignments", {}) if isinstance(clusters, dict) else {}

    for d in drivers:
        driver_id = d["id"] if isinstance(d, dict) else d
        out[driver_id] = {}
        
        driver_known = assignments.get(driver_id) not in (None, "unknown")

        for c in circuits:
            circuit_id = c["id"] if isinstance(c, dict) else c

            if model is None or not driver_known:
                out[driver_id][circuit_id] = "unknown"
                continue

            feats = np.array([_driver_circuit_features(driver_id, c, all_seasons, clusters)])
            pred_delta = float(model.predict(feats)[0])
            score = int(np.clip(50 - pred_delta * 18, 1, 99))
            
            out[driver_id][circuit_id] = {
                "score": score,
                "predicted_delta_s": round(pred_delta, 3)
            }

    return out