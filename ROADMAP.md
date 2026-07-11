# ROADMAP.md

Phase-by-phase build plan. Follow this order exactly — see `AGENTS.md` for the non-negotiables that apply throughout.

---

## Tooling rationale

| Tool | Purpose | Why this one |
|---|---|---|
| Docker + docker-compose | Runs PostgreSQL locally in a container | Consistent environment, no native-install version drift |
| PostgreSQL | Stores the tall fact table + locales/measures/adjacency | Relational integrity + strong window-function support (`RANK() OVER`) needed for ranking badges |
| SQLAlchemy | Python ORM | Standard FastAPI pairing, matches prior project experience |
| Alembic | Schema migrations | Versioned, reversible schema history as the project grows |
| FastAPI | Backend framework | Already the chosen stack; free interactive `/docs` testing UI |
| Pydantic | Request/response validation | Ships with FastAPI, enforces the API contract |
| Uvicorn | ASGI server | Standard FastAPI server |
| python-dotenv | Loads DB credentials from `.env` | Keeps secrets out of source control |
| Vite | Frontend build/dev server | Faster than Create React App, current standard |
| React | UI library | Already the chosen stack |
| react-router-dom | Client-side routing | Required for Tab 1's real `/tab1/state/:id` route (back/forward/refresh must work) |
| @tanstack/react-query | Server-state/caching | Removes hand-written fetch/loading-state boilerplate; handles cache invalidation automatically |
| axios | HTTP client | Convenient JSON handling, natural place for future auth headers |
| react-simple-maps | Map rendering | React wrapper around D3 geo projections; pan/zoom (`ZoomableGroup`) comes free |
| d3-scale | Choropleth color scale | Provides the quantile/Jenks-style scale the design calls for |
| Recharts | Tab 2 charts | Declarative API, animates by default (feeds directly into the wow-factor animation item) |
| Tailwind CSS | Styling | Fast, consistent utility-based styling for a solo developer |

---

## Phase 0 — Environment

- Docker Compose running a Postgres container.
- FastAPI skeleton (`main.py` returning a basic `{"status": "ok"}`).
- Vite + React skeleton (blank page rendering).
- **Done when:** all three run locally without errors.

## Phase 1 — Database & real data

- Alembic migrations for `locales`, `districts`, `measures`, `fact_values`, `state_adjacency` (see `DATABASE.md`).
- Column selection is finalized (`DATABASE.md` §8: `demographics`, `economy`, `literacy`, `infrastructure`, `sanitation`, `drinking_water`) — the seed script's derived-measure list can be built directly against it.
- Seed script: load `india-districts-census-2011.csv` into `districts`, normalize the three legacy state names, aggregate to state-level counts, derive rate measures from aggregated counts (never averaged per-district rates), insert into `fact_values`. See `DATABASE.md` §6 for the exact steps.
- Boundary GeoJSON (2011-era vintage, 35 regions) preprocessed into simplified/full-detail versions via `mapshaper`.
- **Done when:** a raw query returns a correct real value (e.g. Maharashtra's 2011 literacy rate), and that value matches what you get by manually summing/recomputing from the source CSV — worth a one-time manual spot check given the aggregation step is new and easy to get subtly wrong.

## Phase 2 — Backend API

- `/api/v1/analytics`, `/api/v1/presets/closest`, `/api/v1/presets/neighbor` (see `API.md`).
- CORS enabled for the Vite dev origin.
- Verified entirely through `/docs` before any frontend code exists.
- **Done when:** all three endpoints return correct real JSON for any test input.

## Phase 3 — Frontend scaffolding

- Router set up (`/tab1`, `/tab1/state/:id`, `/tab2`).
- React Query provider wired in.
- One test API call confirms frontend↔backend connectivity.
- **Done when:** you can navigate between blank tab pages and see one real API call succeed.

## Phase 4 — Tab 1

Order: map render (simplified topojson) → metric selector + choropleth coloring → labels (ship ISO codes only for v1; add the full three-tier cascade as a refinement pass later, per `DESIGN.md` §A.6) → pan/zoom (`ZoomableGroup`) → click → focused state route → islands inset (a second small `MapView` instance) → quick-zoom shortcut chips.
- **Done when:** the full click → focus → minimize loop works against real data for at least several states.

## Phase 5 — Tab 2

Order: two state selectors → swap/presets/undo → scorecard → diverging bar + radar charts → mini map (`MapView` in highlight mode) → national average + per-capita toggles → the four wow-factor items last (verdict card, ranking badges, chart animations, shared state colors).
- **Done when:** picking any two states renders a complete, correct comparison.

## Phase 6 — Polish

- Loading/error states everywhere via React Query's built-in state flags.
- Real mobile-viewport testing, not just desktop window resizing.
- Manual QA pass against `DESIGN.md`, line by line.

## Phase 7 — RBAC

Only once Phase 6 is done and a real data-curation flow exists to protect. See `RBAC.md` in full — do not start this early.

## Phase 8 — Deployment

Dockerized backend, hosted Postgres (Neon/Supabase), static frontend hosting (Vercel/Netlify). Not a concern until everything works locally.
