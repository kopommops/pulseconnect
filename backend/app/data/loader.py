"""Loads a named JSON dataset, preferring real pipeline output over seed data."""
import json
import os

from app.config import GENERATED_DIR, SEED_DIR


def load(filename):
    generated_path = os.path.join(GENERATED_DIR, filename)
    seed_path = os.path.join(SEED_DIR, filename)
    path = generated_path if os.path.exists(generated_path) else seed_path
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)