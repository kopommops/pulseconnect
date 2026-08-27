"""
Live prediction for the race-outcome model. Returns "unknown" for
everything if no model has been persisted (training gate not yet passed
— see pipeline/build_race_outcome_model.py), and per-driver "unknown" for
anyone below the cold-start real-race threshold. Never fabricates a
probability to fill a gap.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.config import GENERATED_DIR

MODELS_DIR = os.path.join(GENERATED_DIR, "models")
_cache = {}


def _load_model(filename):
    if filename in _cache:
        return _cache[filename]
    path = os.path.join(MODELS_DIR, filename)
    if not os.path.exists(path):
        _cache[filename] = None
        return None
    import joblib
    model = joblib.load(path)
    _cache[filename] = model
    return model


def predict_race_outcome(season, round_no, roster):
    """roster: [{"driver": id, "team": id}, ...] — this weekend's actual
    entries. Returns {driver_id: {"podium_probability", "top5_probability",
    "source"}}; probabilities are None (source "unknown") if the model
    hasn't cleared its deployment gate yet or the driver is cold-start."""
    podium_model = _load_model("race_outcome_podium.pkl")
    top5_model = _load_model("race_outcome_top5.pkl")
    if podium_model is None and top5_model is None:
        return {r["driver"]: {"podium_probability": None, "top5_probability": None, "source": "unknown"} for r in roster}

    pipeline_dir = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline")
    if pipeline_dir not in sys.path:
        sys.path.insert(0, pipeline_dir)
    from feature_engineering import FEATURE_COLUMNS, build_live_features

    features_by_driver = build_live_features(season, round_no, roster)

    out = {}
    for entry in roster:
        did = entry["driver"]
        feats = features_by_driver.get(did)
        if feats is None:
            out[did] = {"podium_probability": None, "top5_probability": None, "source": "unknown"}
            continue
        X = [[feats[c] for c in FEATURE_COLUMNS]]
        podium_p = float(podium_model.predict_proba(X)[0][1]) if podium_model is not None else None
        top5_p = float(top5_model.predict_proba(X)[0][1]) if top5_model is not None else None
        out[did] = {
            "podium_probability": round(podium_p, 4) if podium_p is not None else None,
            "top5_probability": round(top5_p, 4) if top5_p is not None else None,
            "source": "real",
        }
    return out


def model_available():
    return _load_model("race_outcome_podium.pkl") is not None or _load_model("race_outcome_top5.pkl") is not None
