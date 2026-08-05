# PulseConnect v2

Driver–circuit compatibility engine built on real historical F1 data
(FastF1), with a scikit-learn ML layer for driver style clustering and
compatibility prediction. Successor to the non-functional v1 MVP — this
version has a real backend, real (or seed) data, and real models.

## Structure

```
backend/          FastAPI service + FastF1 data pipeline + ML models
  app/
    config.py        season list, 2026 team/driver roster, circuit metadata,
                      FastF1 event-name -> circuit-id resolver
    main.py           FastAPI app, CORS config
    routers/          one file per API resource
    ml/
      clustering.py   KMeans driver-style clustering (real sklearn)
      predict.py      GradientBoostingRegressor compatibility model (real sklearn)
    data/loader.py    reads data/generated/ if present (per file), else data/seed/
  pipeline/
    build_dataset.py REAL pipeline — pulls FastF1 data, computes KPIs, runs ML
    build_seed.py    synthetic seed data, same schema, for offline dev
  data/
    seed/            synthetic sample data (checked in)
    generated/        real pipeline output — small computed JSON files ARE
                      committed (see "Data & deployment" below); the raw
                      FastF1 cache is not
    cache/            FastF1's on-disk session cache (gitignored, large)

frontend/          React + Vite + Tailwind
  src/
    pages/            Landing, DashboardLayout, Compatibility, Consistency, TrackDNA, HeadToHead
    components/       Media (asset fallback), Identity (crest/avatar/circuit art), Viz (gauge/radar/boxplot)
    lib/              api.js client, FiltersContext (7 shared filters)
  public/assets/      drop real driver/team/car/circuit images here (see public/assets/README.md)
```

## About the data

Every response is either **real** (derived from actual FastF1 session data)
or **seed** (synthetic, same shape, clearly stamped `"source": "seed"`) so
the UI can flag it honestly rather than presenting placeholder numbers as
measured ones. Every model, formula, and API route is real and functional;
only the *seed* numbers are placeholders.

```bash
cd backend
pip install -r requirements.txt
python pipeline/build_dataset.py                 # all 6 seasons (slow, hits F1's servers)
python pipeline/build_dataset.py --season 2026   # just one season, for fast iteration
python pipeline/build_dataset.py --force         # rebuild everything, ignoring prior progress
```

This fetches real session data via FastF1 (F1's timing API / Ergast),
computes every KPI from real laps, fits the KMeans clustering and
GradientBoostingRegressor models on real data, and writes JSON to
`data/generated/` — the API automatically prefers that over seed data,
per file, once it exists. No code changes needed.

## Data & deployment: what's committed and why

`data/generated/*.json` (the pipeline's *computed output* — season KPIs,
driver clusters, compatibility predictions) **is committed to git**, even
though it's produced by a script. Two reasons:

1. It's small — the full 6-season KPI set is well under 100KB.
2. FastF1 needs real network access to F1's timing servers to regenerate
   it, which most deploy hosts (and CI runners) won't have. Without
   committing it, a fresh `git clone` + deploy would silently serve seed
   data in production with no error — `loader.py`'s fallback is designed
   to be quiet.

`data/cache/` (FastF1's raw per-session pickle cache — large, and fully
reproducible given network access) is **not** committed.

To refresh production data: re-run `build_dataset.py --force` locally
(or anywhere with real network access), commit the updated
`data/generated/*.json`, and redeploy.

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

### Environment variables

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `ALLOWED_ORIGINS` | backend | `http://localhost:5173` | Comma-separated list of allowed CORS origins. Set to your deployed frontend URL(s) in production. |
| `VITE_API_BASE_URL` | frontend | proxied `/api` in dev | Base URL of the deployed backend API. Set at build time on your frontend host. |

## KPI formulas

- **Consistency**: quartiles (min/Q1/median/Q3/max) of season finishing
  position per driver. Box-plot on the Consistency page.
- **Race pace delta**: driver's median "clean" lap time (`pick_quicklaps()`)
  minus the field's median lap time, per race, averaged over the season
  (`race_pace`) *and* retained per circuit (`race_pace_by_circuit`) so the
  compatibility model has a genuine circuit-conditioned target to learn
  from. Negative = faster than the field.
- **Tyre degradation slope**: linear regression of lap time vs. lap-in-stint
  (first/last lap of each stint dropped, non-green-flag laps excluded via
  `TrackStatus`), in seconds/lap, per compound.
- **Qualifying → race delta**: quali position minus race finish position,
  averaged over the season. Positive = gains positions on race day.
- **Driver style clusters**: KMeans (k=4) on standardized [race pace,
  tyre degradation, quali-race delta, consistency spread] vectors.
- **Compatibility score**: GradientBoostingRegressor trained on real
  driver × circuit *pairs* (each row is a driver's actual pace delta at a
  circuit they raced, joined with that circuit's real features); predicts
  a lap-time delta for any driver/circuit pairing (including ones never
  raced), converted to a 0–100 score for the gauge.

## Unknown data

Any driver before their `debut_season`, or any team before its
`founded_season` (Cadillac, Audi — both 2026), returns `"unknown"` instead
of a fabricated number, all the way through the API and into the UI
(gauges, radars, and box-plot bars all render an explicit "unknown" state
rather than a fake zero).

## Assets

Driver photos, team logos, car cutouts and circuit SVGs are **placeholders**
by design — see `frontend/public/assets/README.md` for the exact file
naming convention. Drop files in and the UI picks them up automatically,
falling back to hand-drawn crests/avatars/line-art for anything missing.

## Known limitations / open items

See `log.txt` for the full debugging history. Worth knowing before you dig
into a specific page:

- A few circuit `type` classifications in `config.py` are judgment calls
  (e.g. Baku categorized `Street` alongside Monaco/Jeddah, despite its long
  high-speed straight) — the compatibility model's circuit-side features
  are only as good as these categories.
- `track_dna.py`'s tyre-wear-index and pit-stop-count figures are
  heuristic, track-type-based estimates (clearly marked
  `"source": "heuristic"`), not yet derived from the real pipeline.

## Stack

- **Backend**: FastAPI, Python, FastF1, scikit-learn, Pandas, NumPy
- **Frontend**: React, Vite, Tailwind CSS, Lucide

## Deployment

- **Frontend**: any static host with a Vite build step (Vercel, Netlify,
  Cloudflare Pages). Set `VITE_API_BASE_URL` to your deployed backend URL.
- **Backend**: any host that runs a Python web service (Render's free tier
  works well for a demo — note it sleeps after 15 min idle with a ~30-60s
  cold start on wake). Set `ALLOWED_ORIGINS` to your deployed frontend URL.
  Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  (no `--reload` in production).
