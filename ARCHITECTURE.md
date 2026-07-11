# ARCHITECTURE.md

System architecture for the Census Analytics Platform. See `AGENTS.md` for build order and non-negotiables, `DATABASE.md` for schema detail, `API.md` for endpoint contracts, `DESIGN.md` for UX behavior.

---

## 1. Stack

| Layer | Technology |
|---|---|
| Frontend framework | React (via Vite) |
| Frontend routing | react-router-dom |
| Server-state / caching | @tanstack/react-query |
| HTTP client | axios |
| Map rendering | react-simple-maps (+ d3-scale for choropleth coloring) |
| Charts | Recharts |
| Styling | Tailwind CSS |
| Backend framework | FastAPI |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation / serialization | Pydantic |
| Database | PostgreSQL |
| Local dev environment | Docker (Postgres container only — app processes run natively) |

Full reasoning for each choice is in the "Tooling rationale" section of `ROADMAP.md`.

---

## 2. High-level data flow

1. Boundary data (India TopoJSON) is preprocessed offline (via `mapshaper`) into two static files: a simplified version for the national map view, and a full-detail version loaded per-state on demand. These are static assets served by the frontend, not fetched from the database.
2. Census 2011 data is sourced as **district-level** rows (`india-districts-census-2011.csv`, 640 districts) and loaded once into Postgres via a seed script that aggregates them up to state/UT level (summed counts, recomputed rates) before writing to the tall/long `fact_values` table. See `DATABASE.md` §§2–6 for the full ETL detail — this is a real transformation step, not a straight import.
3. The frontend calls **one flexible backend endpoint** (`GET /api/v1/analytics`) for all metric data, for both tabs — parameterized by a list of state codes, a year, and an optional rank flag.
4. Tab 2's presets call two small dedicated endpoints (`/api/v1/presets/closest`, `/api/v1/presets/neighbor`) that each return a single matching state code.
5. React Query caches all of the above client-side, handling loading/error states and refetching.

This is intentionally a thin, mostly-stateless backend: almost all "intelligence" (map rendering, coloring, chart layout, preset UI behavior) lives in the frontend, reading from a small number of generic, well-shaped API responses.

---

## 3. Backend structure

```
backend/
  app/
    main.py            # FastAPI app instance, CORS, router registration
    db.py               # SQLAlchemy engine/session, get_db() dependency
    models.py           # SQLAlchemy models: Locale, District, Measure, FactValue, StateAdjacency
    schemas.py          # Pydantic response/request models
    routers/
      analytics.py      # GET /api/v1/analytics
      presets.py        # GET /api/v1/presets/closest, /api/v1/presets/neighbor
      rbac.py            # (Phase 7 only) auth/user management routes
  scripts/
    seed.py              # loads india-districts-census-2011.csv, aggregates to state level, writes fact_values
  alembic/               # migration scripts
  requirements.txt
  .env.example
```

**Why one flexible analytics endpoint instead of one per tab:** Tab 1's focused state view needs one state's full metric set; Tab 2 needs two states' full metric sets side by side. Both are the same underlying query shape — "give me every measure for this list of locales, for this year" — so they're the same endpoint with a different-length `states` parameter. This also means a future 3+ state comparison feature requires zero backend changes.

---

## 4. Frontend structure

```
frontend/
  src/
    main.jsx            # React root, QueryClientProvider, BrowserRouter
    App.jsx              # Route definitions
    api/
      client.js          # axios instance + fetch helper functions
    pages/
      Tab1.jsx
      StateDetail.jsx     # /tab1/state/:id — focused state view
      Tab2.jsx
    components/
      Nav.jsx
      MapView.jsx          # shared by Tab 1 (full choropleth) and Tab 2 (2-state highlight mode)
      MetricSelector.jsx
      ScorecardTable.jsx
      DivergingBarChart.jsx
      RadarChart.jsx
      VerdictCard.jsx
      StateSelector.jsx
    lib/
      stateColors.js      # shared per-state color map, used by both tabs
      colorScale.js        # d3-scale quantile scale for Tab 1's choropleth
```

**Routing** (per `AGENTS.md`'s non-negotiables — Tab 1's focused view must be a real route):
- `/tab1` — national map
- `/tab1/state/:id` — focused state view (foreground map + stats panel, national map dimmed behind)
- `/tab2` — comparison engine

**Shared `MapView` component:** Tab 1 uses it in full choropleth mode (colored by the active metric, click-to-navigate). Tab 2 uses the same component in a "highlight mode" (just outlines State A and State B, no choropleth) for its mini map. One map implementation, two rendering modes — not two separate map components.

---

## 5. Caching strategy

All server data fetching goes through React Query. Query keys are structured so that changing any input (state selection, active metric, year) produces a new cache key and triggers a refetch automatically — e.g. `['analytics', stateCodes, year]`. No manual cache-clearing logic should be needed; this is what React Query is for.

---

## 6. Color consistency across tabs

A single shared module (`lib/stateColors.js`) assigns one fixed color per state/UT, used consistently everywhere a state needs a visual identity: Tab 2's bars, radar lines, and badges, and Tab 1's selection/highlight color. This is independent of Tab 1's choropleth, which stays metric-value-driven (via `lib/colorScale.js`) rather than per-state. Do not let these two coloring systems merge — one is "which color represents this state," the other is "what does this metric's value look like on the map."

---

## 7. Explicit non-goals (for now)

- No RBAC/auth until Phase 7 (see `RBAC.md`).
- No multi-year data or time-series charts (Census 2011 only).
- No accessibility work (documented backlog, not attempted yet).
- No second database (DuckDB or otherwise) — Postgres only, dataset is too small to justify it.
- No deployment/hosting setup until everything works locally (Phase 8, see `ROADMAP.md`).
