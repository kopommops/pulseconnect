"""
PulseConnect v2 API.

Serves generated/ (real FastF1-derived data, present once you've run
pipeline/build_dataset.py) and transparently falls back to seed/ (synthetic,
same shape) so the frontend always has something to render. Every response
in fallback mode carries "source": "seed" so the UI can flag it honestly.

Run: uvicorn app.main:app --reload --port 8000
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import drivers, teams, circuits, compatibility, consistency, track_dna, head_to_head

app = FastAPI(title="PulseConnect v2 API", version="2.0.0")
_origins_env = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(drivers.router, prefix="/api/drivers", tags=["drivers"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])
app.include_router(circuits.router, prefix="/api/circuits", tags=["circuits"])
app.include_router(compatibility.router, prefix="/api/compatibility", tags=["compatibility"])
app.include_router(consistency.router, prefix="/api/consistency", tags=["consistency"])
app.include_router(track_dna.router, prefix="/api/track-dna", tags=["track-dna"])
app.include_router(head_to_head.router, prefix="/api/head-to-head", tags=["head-to-head"])


@app.get("/api/health")
def health():
    return {"status": "ok"}