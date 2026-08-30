"""
Live prediction for the race-outcome model. Two tiers, tried in order:

1. GRID-CONFIRMED — uses this round's actual qualifying result. Only
   possible once qualifying has happened, so only tried if that data
   exists AND the grid-confirmed model cleared its own gate. Stronger
   signal (real grid position beats a rolling average of past ones).
2. FORM-ONLY — the original pre-quali model. Works from Friday, before
   any session has run.

Each field's "source" says which tier actually produced it — the
frontend can (later) show that distinction rather than hiding it.

Returns "unknown" for everything if NEITHER model has cleared its gate,
and per-driver "unknown" for anyone below the cold-start threshold.
Never fabricates a probability to fill a gap.
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
    try:
        model = joblib.load(path)
    except Exception as e:
        print(f"    ! failed to load model {filename}: {e} — serving 'unknown' for it instead")
        model = None
    _cache[filename] = model
    return model


def predict_race_outcome(season, round_no, roster):
    """roster: [{"driver": id, "team": id}, ...] — this weekend's actual
    entries. Returns {driver_id: {"podium_probability", "top5_probability",
    "source"}}."""
    pipeline_dir = os.path.join(os.path.dirname(__file__), "..", "..", "pipeline")
    if pipeline_dir not in sys.path:
        sys.path.insert(0, pipeline_dir)

    grid_podium = _load_model("race_outcome_podium_grid.pkl")
    grid_top5 = _load_model("race_outcome_top5_grid.pkl")
    form_podium = _load_model("race_outcome_podium.pkl")
    form_top5 = _load_model("race_outcome_top5.pkl")

    if not any([grid_podium, grid_top5, form_podium, form_top5]):
        return {r["driver"]: {"podium_probability": None, "top5_probability": None, "source": "unknown"} for r in roster}

    from feature_engineering import FEATURE_COLUMNS, GRID_FEATURE_COLUMNS, build_live_features, build_live_features_grid_confirmed

    grid_features = {}
    if grid_podium is not None or grid_top5 is not None:
        grid_features = build_live_features_grid_confirmed(season, round_no, roster)  # {} if quali hasn't happened yet

    form_features = build_live_features(season, round_no, roster)

    out = {}
    for entry in roster:
        did = entry["driver"]

        # Prefer grid-confirmed when it's both available (quali happened)
        # and this driver isn't cold-start under it.
        gfeats = grid_features.get(did)
        if gfeats is not None and (grid_podium is not None or grid_top5 is not None):
            X = [[gfeats[c] for c in GRID_FEATURE_COLUMNS]]
            podium_p = float(grid_podium.predict_proba(X)[0][1]) if grid_podium is not None else None
            top5_p = float(grid_top5.predict_proba(X)[0][1]) if grid_top5 is not None else None
            if podium_p is not None or top5_p is not None:
                out[did] = {
                    "podium_probability": round(podium_p, 4) if podium_p is not None else None,
                    "top5_probability": round(top5_p, 4) if top5_p is not None else None,
                    "source": "real (grid-confirmed)",
                }
                continue

        ffeats = form_features.get(did)
        if ffeats is not None and (form_podium is not None or form_top5 is not None):
            X = [[ffeats[c] for c in FEATURE_COLUMNS]]
            podium_p = float(form_podium.predict_proba(X)[0][1]) if form_podium is not None else None
            top5_p = float(form_top5.predict_proba(X)[0][1]) if form_top5 is not None else None
            out[did] = {
                "podium_probability": round(podium_p, 4) if podium_p is not None else None,
                "top5_probability": round(top5_p, 4) if top5_p is not None else None,
                "source": "real (form)",
            }
            continue

        out[did] = {"podium_probability": None, "top5_probability": None, "source": "unknown"}

    return out


def model_available():
    return _load_model("race_outcome_podium.pkl") is not None or _load_model("race_outcome_top5.pkl") is not None
