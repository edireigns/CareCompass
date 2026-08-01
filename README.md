# CareCompass

A working scaffold for CareCompass: a platform that helps patients choose a
hospital based on quality, outcomes, wait time, distance, and insurance —
not just proximity.

This is a **runnable code scaffold**, not a finished product. It implements
the full request path end-to-end (React → FastAPI → Postgres) with mock
data standing in for the CMS/CDC ETL pipeline, so you have something real
to build on immediately.

## What's actually implemented

- **Backend**: FastAPI app with all 8 endpoints from the spec (`/search`,
  `/nearby`, `/hospital/{id}`, `/compare`, `/recommend`, `/specialties`,
  `/insurance`, `/rankings`), a repository layer, a service layer, and a
  working Smart Ranking Algorithm with the spec's default weights
  (35% quality / 25% wait time / 20% distance / 10% satisfaction /
  10% readmission), customizable via query params.
- **Database**: SQLAlchemy models for all 9 tables from the spec
  (`hospitals`, `hospital_quality`, `hospital_outcomes`,
  `patient_experience`, `insurance`, `specialties`, `locations`,
  `wait_time_estimates`, `dataset_metadata`), an Alembic setup, and a seed
  script that loads 5 realistic mock hospitals so the API returns real
  rows immediately.
- **Frontend**: React + TypeScript + Tailwind + React Query, with all 8
  pages from the spec routed and functional against the live API (Search,
  Hospital Details, Compare, AI Assistant, Rankings, Analytics, Admin,
  Landing). Ranking weight sliders are built; wiring their values into the
  live query is flagged as a `NOTE` in `RankingsPage.tsx`.
- **Docker Compose**: one command brings up Postgres, Redis, backend, and
  frontend together, seeding the database automatically.
- **Tests**: unit tests for the ranking algorithm (the highest-value
  logic to pin down early).

## What's intentionally stubbed

- **ETL pipeline**: `scripts/seed.py` loads mock data in the shape the
  real pipeline will produce. The actual CMS Care Compare / CDC fetch +
  clean + load pipeline isn't built yet — that's a separate, sizeable
  piece of work (see Roadmap below).
- **AI Assistant**: `/recommend` does real work — it filters and ranks
  candidate hospitals using the same logic as `/search`/`/rankings` — but
  returns a templated sentence instead of an LLM-generated summary. The
  service function (`HospitalService.recommend`) has a docstring marking
  exactly where to add an Anthropic API call, and is deliberately
  structured so the LLM only *summarizes* pre-filtered factual data
  rather than inventing anything.
- **Auth / user accounts**: not started (spec lists this under
  "nice-to-have").
- **Interactive map (Leaflet)**: dependency is wired into `package.json`
  and CSS is imported in `index.html`, but no map component is built yet.

## Getting started

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend docs (Swagger): http://localhost:8000/docs
- Postgres is seeded automatically on first boot.

### Option B — Run locally without Docker

**Backend:**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then point DATABASE_URL at a local Postgres
python -m scripts.seed
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Running tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

## Architecture

```
carecompass/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router wiring
│   │   ├── core/config.py     # env-driven settings (pydantic-settings)
│   │   ├── db/session.py      # SQLAlchemy engine/session/Base
│   │   ├── models/            # ORM models (9 tables)
│   │   ├── schemas/           # Pydantic request/response shapes
│   │   ├── repositories/      # ONLY layer that writes SQL queries
│   │   ├── services/          # business logic (ranking, distance, comparison)
│   │   ├── api/routes/        # one file per endpoint group
│   │   └── data/              # mock dataset used by scripts/seed.py
│   ├── scripts/seed.py        # loads mock data into Postgres
│   ├── tests/                 # pytest unit tests
│   └── alembic/               # migrations (autogenerate against models)
├── frontend/
│   └── src/
│       ├── pages/             # one file per route in the spec
│       ├── components/        # HospitalCard, ComparisonTable, etc.
│       ├── hooks/useHospitals.ts  # React Query hooks, one per endpoint
│       ├── api/client.ts      # single axios instance
│       └── types/hospital.ts  # TS types mirroring backend schemas
└── docker-compose.yml
```

**Why repository + service layers?** Routes never touch SQLAlchemy
directly. `HospitalRepository` is the only place that writes queries;
`HospitalService` composes repository calls with business logic (distance
math, score computation). This means the ranking algorithm can be unit
tested (see `tests/test_ranking_service.py`) without a database, and the
persistence layer can change without touching business logic.

**Why does `/recommend` not call an LLM yet?** The spec is explicit that
"the AI should summarize the supporting data rather than invent
information." The scaffold does the *grounding* step for real — it
reuses the same search/ranking logic as every other endpoint to select
factual candidate hospitals — and stops one step short of the actual
LLM call, since that requires an API key and a prompt design decision
that's better made deliberately than defaulted.

## Data model notes

- `overall_score` is computed on read, not stored — it depends on the
  user's location and chosen weights, so persisting it would mean
  recomputing on every weight change anyway.
- `wait_time_estimates` is explicitly called out in the spec as
  "prototype values" — there's no real-time ER wait feed integrated.
- `dataset_metadata` exists in the schema now so the eventual ETL
  pipeline and the "Admin Data Refresh" page have somewhere to write
  freshness/status to, even though nothing populates it yet.

## Roadmap (next milestones)

1. **ETL pipeline** — pull CMS Care Compare + CMS Hospital General
   Information via their public API, clean/normalize with pandas, load
   into the schema above, write freshness rows to `dataset_metadata`.
   Schedule via GitHub Actions or a cron container.
2. **Wire ranking weights** from `RankingsPage.tsx` into the `/rankings`
   query params (currently computed with defaults only).
3. **Map integration** — Leaflet component on `SearchPage` plotting
   results, using each hospital's `location.latitude/longitude`.
4. **LLM-backed `/recommend`** — call the Anthropic API with the
   pre-filtered `candidates` list as context, per the docstring in
   `HospitalService.recommend`.
5. **Auth + saved hospitals** (nice-to-have in spec).
6. **CI** — GitHub Actions running `pytest` (backend) and `tsc --noEmit`
   (frontend) on every PR.

## Deployment

Both `backend/Dockerfile` and `frontend/Dockerfile` are production-ready
multi-stage-friendly builds. For Railway or Render:
- Deploy `backend/` as a web service, set `DATABASE_URL` to the
  provider's managed Postgres connection string, and run
  `python -m scripts.seed` once (or replace with the real ETL pipeline).
- Deploy `frontend/` as a static site (`npm run build` → serve `dist/`),
  setting `VITE_API_BASE_URL` to the deployed backend's URL.