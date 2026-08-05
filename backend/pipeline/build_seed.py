"""
Builds the SEED dataset: synthetic data in the exact same JSON shape that
build_dataset.py produces from real FastF1 data. This exists purely so the
frontend has something realistic to render before you've run the real
pipeline against a machine with normal internet access.

Every file this writes is clearly a stand-in — `"source": "seed"` is stamped
into each JSON payload so the frontend can show a "sample data" indicator,
and it never overwrites backend/data/generated/ (real pipeline output).

Run: python pipeline/build_seed.py
"""
import json
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.config import SEASONS, DRIVERS, TEAMS, CIRCUITS, SEED_DIR, UNKNOWN

random.seed(7)

TRACK_TYPE_DEMAND = {
    "Power":      {"braking": 58, "traction": 55, "apexSpeed": 94, "tyreMgmt": 50, "aero": 35, "technical": 40},
    "Street":     {"braking": 87, "traction": 62, "apexSpeed": 28, "tyreMgmt": 58, "aero": 82, "technical": 93},
    "Technical":  {"braking": 62, "traction": 70, "apexSpeed": 72, "tyreMgmt": 62, "aero": 87, "technical": 86},
    "Balanced":   {"braking": 60, "traction": 68, "apexSpeed": 76, "tyreMgmt": 74, "aero": 78, "technical": 62},
    "High-Speed": {"braking": 64, "traction": 60, "apexSpeed": 91, "tyreMgmt": 64, "aero": 68, "technical": 54},
    "Mixed":      {"braking": 70, "traction": 74, "apexSpeed": 66, "tyreMgmt": 70, "aero": 66, "technical": 70},
}

# hand-set base skill (0-100) per driver, used to derive every synthetic
# stat below with a bit of controlled noise so numbers look plausible and
# internally consistent rather than pure random
BASE_SKILL = {
    "VER": 96, "HAM": 90, "ALO": 89, "LEC": 88, "NOR": 87, "RUS": 85, "PIA": 85,
    "SAI": 83, "GAS": 80, "ALB": 80, "HUL": 79, "PER": 82, "OCO": 78, "STR": 72,
    "TSU": 76, "BOT": 80, "ANT": 78, "HAD": 74, "LAW": 75, "COL": 70, "BOR": 68,
    "BEA": 70, "LIN": 65,
}


def has_debuted(driver, season):
    return season >= driver["debut_season"]


def team_exists(team, season):
    return team["founded_season"] is None or season >= team["founded_season"]


def noisy(base, spread=6):
    return round(base + random.uniform(-spread, spread), 3)


# small per-driver, per-track-type bias so synthetic per-circuit pace isn't
# just the season average repeated — mirrors the real driver x circuit
# interaction the ML model is meant to learn from race_pace_by_circuit.
# Values are in seconds/lap, same sign convention as race_pace (negative = faster).
TRACK_TYPE_BIAS = {
    "VER": {"Street": -0.25, "Power": 0.05},
    "HAM": {"Street": -0.15, "Technical": -0.1},
    "ALO": {"Street": -0.2, "Technical": -0.15},
    "LEC": {"Street": -0.1, "High-Speed": 0.05},
    "NOR": {"Balanced": -0.1},
    "PER": {"Street": 0.15, "Power": -0.1},
}


def build_season_kpis():
    all_seasons = {}
    for season in SEASONS:
        consistency, race_pace, race_pace_by_circuit, tyre_deg, quali_race = {}, {}, {}, {}, {}
        for d in DRIVERS:
            if not has_debuted(d, season):
                consistency[d["id"]] = UNKNOWN
                race_pace[d["id"]] = UNKNOWN
                race_pace_by_circuit[d["id"]] = UNKNOWN
                tyre_deg[d["id"]] = UNKNOWN
                quali_race[d["id"]] = UNKNOWN
                continue
            skill = BASE_SKILL.get(d["id"], 70)
            median_pos = round(21 - (skill / 100) * 19, 1)
            spread = round(8 - (skill / 100) * 5, 1)
            consistency[d["id"]] = {
                "min": max(1, int(median_pos - spread - 2)),
                "q1": round(max(1, median_pos - spread / 2), 1),
                "median": median_pos,
                "q3": round(min(20, median_pos + spread / 2), 1),
                "max": min(20, int(median_pos + spread + 3)),
                "n_races": random.randint(18, 24),
            }
            base_pace = (100 - skill) * 0.018
            race_pace[d["id"]] = noisy(base_pace, 0.15)
            bias = TRACK_TYPE_BIAS.get(d["id"], {})
            race_pace_by_circuit[d["id"]] = {
                c["id"]: noisy(base_pace + bias.get(c["type"], 0.0), 0.1) for c in CIRCUITS
            }
            tyre_deg[d["id"]] = {
                "SOFT": noisy(0.045 - skill * 0.0002, 0.01),
                "MEDIUM": noisy(0.030 - skill * 0.00015, 0.008),
                "HARD": noisy(0.018 - skill * 0.0001, 0.006),
            }
            quali_race[d["id"]] = noisy((skill - 75) * 0.03, 0.8)
        all_seasons[str(season)] = {
            "consistency": consistency, "race_pace": race_pace,
            "race_pace_by_circuit": race_pace_by_circuit,
            "tyre_degradation": tyre_deg, "quali_race_delta": quali_race,
            "source": "seed",
        }
    return all_seasons


def build_driver_clusters():
    labels = {
        "0": "Smooth & Consistent", "1": "Aggressive Attacker",
        "2": "Technical Precision", "3": "Raw Pace / High Variance",
    }
    assignments = {}
    for d in DRIVERS:
        if d["debut_season"] > 2026:
            assignments[d["id"]] = "unknown"
            continue
        skill = BASE_SKILL.get(d["id"], 70)
        if skill >= 88:
            assignments[d["id"]] = 3
        elif skill >= 80:
            assignments[d["id"]] = 1
        elif skill >= 74:
            assignments[d["id"]] = 2
        else:
            assignments[d["id"]] = 0
    return {"labels": labels, "assignments": assignments, "source": "seed"}


def build_compatibility_predictions(clusters):
    out = {"source": "seed"}
    for d in DRIVERS:
        out[d["id"]] = {}
        skill = BASE_SKILL.get(d["id"], 70)
        for c in CIRCUITS:
            demand = TRACK_TYPE_DEMAND.get(c["type"], TRACK_TYPE_DEMAND["Balanced"])
            fit = sum(demand.values()) / len(demand) / 100
            score = int(min(99, max(1, skill * 0.75 + fit * 25 + random.uniform(-4, 4))))
            delta = round((score - 50) / -40, 3)
            out[d["id"]][c["id"]] = {"score": score, "predicted_delta_s": delta}
    return out


def build_driver_traits():
    """Six-axis trait vectors (0-100) derived from base skill + role flavor,
    used directly by the compatibility radar on the frontend."""
    out = {}
    for d in DRIVERS:
        skill = BASE_SKILL.get(d["id"], 70)
        out[d["id"]] = {
            "braking": int(min(99, skill + random.uniform(-8, 8))),
            "traction": int(min(99, skill + random.uniform(-8, 8))),
            "apexSpeed": int(min(99, skill + random.uniform(-8, 8))),
            "tyreMgmt": int(min(99, skill + random.uniform(-10, 6))),
            "aero": int(min(99, skill + random.uniform(-8, 8))),
            "technical": int(min(99, skill + random.uniform(-6, 8))),
        }
    return out


def main():
    os.makedirs(SEED_DIR, exist_ok=True)

    season_kpis = build_season_kpis()
    clusters = build_driver_clusters()
    predictions = build_compatibility_predictions(clusters)
    traits = build_driver_traits()

    files = {
        "season_kpis.json": season_kpis,
        "driver_clusters.json": clusters,
        "compatibility_predictions.json": predictions,
        "driver_traits.json": traits,
        "drivers.json": {"source": "seed", "data": DRIVERS},
        "teams.json": {"source": "seed", "data": TEAMS},
        "circuits.json": {"source": "seed", "data": CIRCUITS},
    }
    for name, payload in files.items():
        path = os.path.join(SEED_DIR, name)
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()