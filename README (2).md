# PulseConnect v2

Driver–circuit compatibility engine built on real historical F1 data
(FastF1), with a scikit-learn ML layer for driver style clustering and
compatibility prediction. Successor to the non-functional v1 MVP — this
version has a real backend, real (or seed) data, and real models.

## Structure

```
backend/          FastAPI service + FastF1 data pipeline + ML models
  app/
    config.py        season list, 2026 team/driver roster, circuit metadata
    main.py           FastAPI app
    routers/          one file per API resource
    ml/
      clustering.py   KMeans driver-style clustering (real sklearn)
      predict.py       GradientBoostingRegressor compatibility model (real sklearn)
    data/loader.py    reads data/generated/ if present, else data/seed/
  pipeline/
    build_dataset.py REAL pipeline — pulls FastF1 data, computes KPIs, runs ML
    build_seed.py    synthetic seed data, same schema, for offline dev
  data/
    seed/            synthetic sample data (checked in)
    generated/        real pipeline output (gitignored, run the pipeline to populate)
    cache/            FastF1's on-disk session cache

frontend/          React + Vite + Tailwind
  src/
    pages/            Landing, DashboardLayout, Compatibility, Consistency, TrackDNA, HeadToHead
    components/       Media (asset fallback), Identity (crest/avatar/circuit art), Viz (gauge/radar/boxplot)
    lib/              api.js client, FiltersContext (7 shared filters)
  public/assets/      drop real driver/team/car/circuit images here (see public/assets/README.md)
```

## IMPORTANT: about the data

**This sandbox cannot reach FastF1's real data sources** (only package
registries are reachable here), so everything you're seeing right now is
the **seed dataset** — synthetic numbers in the exact shape the real
pipeline produces, clearly stamped `"source": "seed"` in every API
response. Every model, formula and API route is real and functional; only
the numbers are placeholders until you run the real pipeline on a machine
with normal internet access:

```bash
cd backend
pip install -r requirements.txt
python pipeline/build_dataset.py            # all 6 seasons (slow, hits F1's servers)
python pipeline/build_dataset.py --season 2026   # just one season, for fast iteration
```

This fetches real session data via FastF1 (which pulls from F1's timing
API and Ergast), computes every KPI from real laps, fits the KMeans
clustering and GradientBoostingRegressor models on real data, and writes
JSON to `data/generated/` — the API automatically prefers that over the
seed data once it exists. No code changes needed.

## Running locally

```bash
# backend
cd backend
pip install -r requirements.txt
python pipeline/build_seed.py        # or build_dataset.py for real data
uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev                          # http://localhost:5173, proxies /api to :8000
```

## KPI formulas

- **Consistency**: quartiles (min/Q1/median/Q3/max) of season finishing
  position per driver. Box-plot on the Consistency page.
- **Race pace delta**: driver's median "clean" lap time (`pick_quicklaps()`)
  minus the field's median lap time, per race, averaged over the season.
  Negative = faster than the field.
- **Tyre degradation slope**: linear regression of lap time vs. lap-in-stint
  (first/last lap of each stint dropped), in seconds/lap, per compound.
- **Qualifying → race delta**: quali position minus race finish position,
  averaged over the season. Positive = gains positions on race day.
- **Driver style clusters**: KMeans (k=4) on standardized [race pace,
  tyre degradation, quali-race delta, consistency spread] vectors.
- **Compatibility score**: GradientBoostingRegressor trained on real
  driver × circuit-type race-pace outcomes; predicts a lap-time delta for
  any driver/circuit pairing (including ones never raced), converted to a
  0–100 score for the gauge.

## Unknown data

Any driver before their `debut_season`, or any team before its
`founded_season` (Cadillac, Audi — both 2026), returns `"unknown"` instead
of a fabricated number, all the way through the API and into the UI
(gauges, radars and box-plot bars all render an explicit "unknown" state
rather than a fake zero).

## Assets

Driver photos, team logos, car cutouts and circuit SVGs are **placeholders**
by design — see `frontend/public/assets/README.md` for the exact file
naming convention. Drop files in and the UI picks them up automatically,
falling back to hand-drawn crests/avatars/line-art for anything missing.
