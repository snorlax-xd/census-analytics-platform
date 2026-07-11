# AGENTS.md

Instructions for any coding agent (or human) working in this repository. Read this first. The other files in this set (`ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `DESIGN.md`, `RBAC.md`, `SKILLS.md`, `ROADMAP.md`) contain the full detail behind every decision referenced here.

---

## What this project is

Census Analytics Platform: a two-tab web app for exploring and comparing Indian Census 2011 data.
- **Tab 1** — a national map of India, colored by a selectable metric, click-through to a focused single-state view.
- **Tab 2** — a fixed two-state side-by-side comparison with charts, presets, and a scorecard.

Stack: **React (Vite) + FastAPI + PostgreSQL.** Full rationale for every tool choice is in `ARCHITECTURE.md`.

---

## Build order — follow `ROADMAP.md` exactly

Do not build out of order. Each phase must be verifiably working before the next begins:

1. Environment (Docker Postgres, FastAPI skeleton, Vite skeleton)
2. Database schema + real Census 2011 data loaded
3. Backend API (single analytics endpoint + two preset endpoints)
4. Frontend scaffolding (routing, React Query, one working API call)
5. Tab 1
6. Tab 2
7. Polish pass
8. RBAC — **only after Phase 6 is done and a real data-curation flow exists to protect.** Do not add auth/JWT/login scaffolding before this. See `RBAC.md` for why.
9. Deployment — last, only once everything works locally.

If asked to "just start building the frontend" before the backend/database phases are done, push back and explain the dependency — Tab 1 and Tab 2 both read from the same live API, there's nothing real to render against until Phase 2 is done.

---

## Non-negotiable decisions

These were arrived at after explicit stress-testing in design discussion. Do not silently "improve" or revert them:

- **Tab 2 is fixed at exactly two states (State A, State B).** Not a variable-length chip list. This was a deliberate simplification — do not reintroduce a 2–4 state cap, chip removal, or anchor-reassignment logic.
- **No hover-based interaction anywhere in Tab 1.** Click/tap only, on all devices identically.
- **No dropdown/search as the fix for hard-to-click small states in Tab 1.** Use pan/zoom + quick-zoom shortcut chips instead. The only permanent exception is a fixed inset box for the offshore islands (Andaman & Nicobar, Lakshadweep) — every other small state (North-East cluster, Goa, Delhi, Chandigarh, etc.) is handled by interactive zoom, not a static inset panel or leader-line callout as the default.
- **The backend has one flexible analytics endpoint** (`/api/v1/analytics?states=...`), not separate endpoints per tab or per feature. It accepts an arbitrary-length state list even though Tab 2's frontend only ever sends two — this keeps a future 3+ state comparison a frontend-only change.
- **Every measure needs a `higher_is_better` field** (nullable: `true`/`false`/`null`). This is required for the verdict card and ranking badges to know whether "higher" means "winning" for a given metric — don't skip this when adding new measures.
- **Data is Census 2011 only for now.** Do not build multi-year comparison logic; the schema anticipates it (via the measure/year structure) but no UI or query should assume more than one year exists yet.
- **The primary data source is district-level** (`india-districts-census-2011.csv`, 640 districts across 35 states/UTs), not state-level. State/UT values in `fact_values` must be produced by aggregating district rows during ETL — counts summed, rates recomputed from summed counts, never averaged directly across districts. See `DATABASE.md` §6.
- **Map and data vintage must match: 2011-era state/UT boundaries (35 regions), not the current 36.** The source data predates Telangana, the J&K/Ladakh split, and the DNH/Daman & Diu merger — rendering current boundaries against this data would misrepresent it. See `DATABASE.md` §2.
- **`population_density` cannot be built until a supplementary state land-area table is sourced.** The primary CSV has no area/km² column at all. Don't silently ship a metric option that has no way to resolve — either source the area data first or explicitly drop the metric from v1. See `DATABASE.md` §3/§8.
- **No DuckDB or second database.** Postgres is the only data store. The dataset (a few hundred to low-thousands of rows) is far too small for a columnar analytics engine to provide any benefit, and running two databases in sync is unjustified complexity here.
- **Accessibility (screen readers, keyboard nav, colorblind-safe palettes) is explicitly out of scope for now** — a documented backlog item, not something to skip silently or something to build unprompted.
- **RBAC gates only the data-curation side** (uploading data, editing measures, publishing versions). Both tabs are public read access, always, with no login required.

If a task seems to require violating one of these, stop and flag it rather than proceeding — these were decided deliberately, not by default.

---

## Conventions

**Backend (FastAPI):**
- One router file per resource under `app/routers/` (`analytics.py`, `presets.py`, and later `rbac.py`).
- SQLAlchemy models in `app/models.py`, Pydantic response/request schemas in `app/schemas.py` — keep these separate, never return a raw SQLAlchemy model from an endpoint.
- All schema changes go through an Alembic migration. Never hand-edit the database schema directly.
- Every new endpoint gets tested via the `/docs` Swagger UI before any frontend code calls it.

**Frontend (React):**
- Functional components with hooks only.
- All server data fetching goes through `@tanstack/react-query` (`useQuery`/`useMutation`) — no raw `useEffect` + `useState` fetch patterns.
- Styling via Tailwind utility classes — avoid introducing a separate CSS-in-JS system.
- Any state color (for a given state's bars, radar lines, map highlight) must come from the single shared `stateColors` module — never hardcode a hex value per component. See `DESIGN.md` §6.8.4.

**General:**
- Prefer small, verifiable steps. After each phase, there should be something a human can actually click through and see working — not just code that compiles.
- When in doubt about a UX detail, check `DESIGN.md` first — it documents not just what was decided but why, including what alternatives were rejected and why.
