# backend/pipeline/build_grid_confirmed_model.py — NEW FILE
"""
Trains the GRID-CONFIRMED podium/top-5 classifiers — same problem as
build_race_outcome_model.py, but using each round's ACTUAL qualifying
result as a feature instead of only a rolling average from past rounds.

Why this is a separate model, not a feature added to the existing one:
grid position for the round being predicted is only knowable once
qualifying for that round has actually happened — Saturday afternoon,
not Friday. The original model has to work without it (pre-quali);
this one only ever runs post-quali. Two models, two serving windows,
same evaluation discipline (temporal holdout, precision@k, hard gate).

Separate .pkl files (race_outcome_podium_grid.pkl /
race_outcome_top5_grid.pkl) so this NEVER overwrites the form-only
models — app/ml/race_outcome.py prefers this one automatically once
quali data exists for the round being served, falling back to the
form-only model otherwise.

Usage:
    cd backend
    python pipeline/build_grid_confirmed_model.py
    python pipeline/build_grid_confirmed_model.py --test-season 2025
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import GENERATED_DIR, PODIUM_PRECISION_TARGET, TOP5_PRECISION_TARGET
from feature_engineering import GRID_FEATURE_COLUMNS, build_training_rows_grid_confirmed, rows_to_matrix

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier

MODELS_DIR = os.path.join(GENERATED_DIR, "models")


def precision_at_k(rows, probs, label_key, k):
    by_race = {}
    for row, p in zip(rows, probs):
        key = (row["season"], row["round"])
        by_race.setdefault(key, []).append((row["driver"], p, row[label_key]))

    race_scores = []
    for key, entries in by_race.items():
        if len(entries) < k:
            continue
        actual_top = {d for d, _, lbl in entries if lbl == 1}
        if len(actual_top) == 0:
            continue
        predicted_top = {d for d, _, _ in sorted(entries, key=lambda e: -e[1])[:k]}
        race_scores.append(len(predicted_top & actual_top) / k)

    if not race_scores:
        return None, 0
    return sum(race_scores) / len(race_scores), len(race_scores)


def train_and_pick_best(X_train, y_train, X_test, test_rows, label_key, k):
    candidates = {
        "random_forest": RandomForestClassifier(
            n_estimators=500, max_depth=7, min_samples_leaf=3, class_weight="balanced",
            max_features=0.8, random_state=42, n_jobs=-1,
        ),
        #"gradient_boosting": GradientBoostingClassifier(
        #    n_estimators=400, max_depth=4, learning_rate=0.03,
        #    max_features=0.8, subsample=0.8, random_state=42,
        #),
    }
    results = {}
    for name, clf in candidates.items():
        clf.fit(X_train, y_train)
        probs = clf.predict_proba(X_test)[:, 1] if len(set(y_train)) > 1 else [0.0] * len(X_test)
        score, n_races = precision_at_k(test_rows, probs, label_key, k)
        results[name] = {"model": clf, "precision_at_k": score, "n_test_races": n_races}
        print(f"    {name}: precision@{k} = {score if score is None else round(score, 4)} (over {n_races} held-out races)")

    best_name = max(results, key=lambda n: (results[n]["precision_at_k"] or -1))
    return best_name, results[best_name]


def print_feature_importances(name, result):
    model = result["model"]
    if not hasattr(model, "feature_importances_"):
        return
    pairs = sorted(zip(GRID_FEATURE_COLUMNS, model.feature_importances_), key=lambda p: -p[1])
    print(f"    feature importances ({name}):")
    for feat, imp in pairs:
        print(f"      {feat:30s} {imp:.4f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-season", type=int, default=None)
    args = parser.parse_args()

    print("Building grid-confirmed feature rows (rounds with a real quali result only)...")
    rows = build_training_rows_grid_confirmed()
    if not rows:
        print("No grid-confirmed rows available — need real race_results.json with quali data.")
        return
    seasons_present = sorted({r["season"] for r in rows})
    print(f"{len(rows)} real, non-cold-start rows across seasons {seasons_present}")

    test_season = args.test_season or (seasons_present[-2] if len(seasons_present) >= 2 else seasons_present[-1])
    train_rows = [r for r in rows if r["season"] < test_season]
    test_rows = [r for r in rows if r["season"] == test_season]
    print(f"Temporal holdout: train on seasons < {test_season} ({len(train_rows)} rows), "
          f"test on {test_season} only ({len(test_rows)} rows)")

    if not train_rows or not test_rows:
        print("Not enough data on either side of the split.")
        return

    X_train, y_train_podium, y_train_top5, _ = rows_to_matrix(train_rows, GRID_FEATURE_COLUMNS)
    X_test, _, _, _ = rows_to_matrix(test_rows, GRID_FEATURE_COLUMNS)

    print(f"\n== Grid-confirmed podium model (precision@3, target >= {PODIUM_PRECISION_TARGET}) ==")
    podium_name, podium_result = train_and_pick_best(X_train, y_train_podium, X_test, test_rows, "podium", 3)
    print(f"  best: {podium_name} -> {podium_result['precision_at_k']}")
    print_feature_importances(podium_name, podium_result)

    print(f"\n== Grid-confirmed top-5 model (precision@5, target >= {TOP5_PRECISION_TARGET}) ==")
    top5_name, top5_result = train_and_pick_best(X_train, y_train_top5, X_test, test_rows, "top5", 5)
    print(f"  best: {top5_name} -> {top5_result['precision_at_k']}")
    print_feature_importances(top5_name, top5_result)

    podium_pass = (podium_result["precision_at_k"] or 0) >= PODIUM_PRECISION_TARGET
    top5_pass = (top5_result["precision_at_k"] or 0) >= TOP5_PRECISION_TARGET

    print(f"\n== Gate (decoupled) ==")
    print(f"  podium precision@3 = {podium_result['precision_at_k']}  {'PASS' if podium_pass else 'FAIL'} (target {PODIUM_PRECISION_TARGET})")
    print(f"  top5   precision@5 = {top5_result['precision_at_k']}  {'PASS' if top5_pass else 'FAIL'} (target {TOP5_PRECISION_TARGET})")

    if not podium_pass and not top5_pass:
        print("\nBOTH FAILED — nothing written. Form-only model (if it passed) keeps serving pre-quali;")
        print("neither grid-confirmed file is written, so post-quali serving falls back to form-only too.")
        return

    os.makedirs(MODELS_DIR, exist_ok=True)
    import joblib
    X_all, y_all_podium, y_all_top5, _ = rows_to_matrix(rows, GRID_FEATURE_COLUMNS)
    model_card_path = os.path.join(MODELS_DIR, "model_card_grid.json")
    model_card = {
        "trained_on_seasons": seasons_present,
        "test_season_holdout": test_season,
        "feature_columns": GRID_FEATURE_COLUMNS,
        "gate": {"podium_target": PODIUM_PRECISION_TARGET, "top5_target": TOP5_PRECISION_TARGET},
        "n_training_rows_final_fit": len(rows),
    }

    if podium_pass:
        print("\nGrid podium gate PASSED. Refitting on all data and persisting...")
        final_podium = (RandomForestClassifier(n_estimators=500, max_depth=7, min_samples_leaf=3, class_weight="balanced", max_features=0.8, random_state=42, n_jobs=-1)
                         if podium_name == "random_forest" else
                         GradientBoostingClassifier(n_estimators=400, max_depth=4, learning_rate=0.03, max_features=0.8, subsample=0.8, random_state=42))
        final_podium.fit(X_all, y_all_podium)
        joblib.dump(final_podium, os.path.join(MODELS_DIR, "race_outcome_podium_grid.pkl"))
        model_card["podium_model"] = {
            "algorithm": podium_name, "passed": True,
            "holdout_precision_at_3": podium_result["precision_at_k"],
            "holdout_test_races": podium_result["n_test_races"],
            "feature_importances": dict(zip(GRID_FEATURE_COLUMNS, [round(float(v), 4) for v in final_podium.feature_importances_])),
        }
    else:
        print("\nGrid podium gate FAILED — race_outcome_podium_grid.pkl NOT written.")
        stale = os.path.join(MODELS_DIR, "race_outcome_podium_grid.pkl")
        if os.path.exists(stale):
            os.remove(stale)
            print("  (removed stale previously-passing grid podium model)")
        model_card["podium_model"] = {"algorithm": podium_name, "passed": False, "holdout_precision_at_3": podium_result["precision_at_k"]}

    if top5_pass:
        print("Grid top-5 gate PASSED. Refitting on all data and persisting...")
        final_top5 = (RandomForestClassifier(n_estimators=500, max_depth=7, min_samples_leaf=3, class_weight="balanced", max_features=0.8, random_state=42, n_jobs=-1)
                      if top5_name == "random_forest" else
                      GradientBoostingClassifier(n_estimators=400, max_depth=4, learning_rate=0.03, max_features=0.8, subsample=0.8, random_state=42))
        final_top5.fit(X_all, y_all_top5)
        joblib.dump(final_top5, os.path.join(MODELS_DIR, "race_outcome_top5_grid.pkl"))
        model_card["top5_model"] = {
            "algorithm": top5_name, "passed": True,
            "holdout_precision_at_5": top5_result["precision_at_k"],
            "holdout_test_races": top5_result["n_test_races"],
            "feature_importances": dict(zip(GRID_FEATURE_COLUMNS, [round(float(v), 4) for v in final_top5.feature_importances_])),
        }
    else:
        print("Grid top-5 gate FAILED — race_outcome_top5_grid.pkl NOT written.")
        stale = os.path.join(MODELS_DIR, "race_outcome_top5_grid.pkl")
        if os.path.exists(stale):
            os.remove(stale)
            print("  (removed stale previously-passing grid top5 model)")
        model_card["top5_model"] = {"algorithm": top5_name, "passed": False, "holdout_precision_at_5": top5_result["precision_at_k"]}

    with open(model_card_path, "w") as f:
        json.dump(model_card, f, indent=2)

    print(f"\nWrote model_card_grid.json. Restart the API to serve whichever grid-confirmed model(s) passed.")


if __name__ == "__main__":
    main()