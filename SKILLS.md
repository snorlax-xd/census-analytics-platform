# SKILLS.md

Step-by-step patterns for recurring development tasks in this repo. When asked to do one of these things, follow the pattern here rather than improvising a new structure each time — consistency matters more than cleverness in a project this size.

---

## Adding a new measure (metric)

1. Decide if it's **derived** (a rate/percentage computed from raw counts, e.g. `literacy_rate`) or **raw** (loaded from one summed source column, e.g. `population`) — set `is_derived` accordingly. See `DATABASE.md` §3/§6.
2. Add it to `measures`: `code`, `name`, `unit`, `category` (one of `demographics`/`economy`/`literacy`/`infrastructure`/`sanitation`/`drinking_water`), and — critically — `higher_is_better` (`true`, `false`, or `null` if non-directional). Never leave this unset; see `AGENTS.md` non-negotiables.
3. In `scripts/seed.py`, map it to its source column(s) in `india-districts-census-2011.csv`. If it's a raw count, sum across each state's districts. If it's derived, compute it from already-aggregated state-level counts — **never average a per-district rate directly**, this misweights small and large districts equally (see `DATABASE.md` §6, step 2). Insert the result into `fact_values` for each locale.
4. If it belongs in Tab 1's metric selector, add it to the frontend's metric options list and confirm the choropleth color scale (`lib/colorScale.js`) handles its value range sensibly (check for skew — decide if it needs a quantile scale or a diverging scale, per `DESIGN.md` §A.7).
5. If it should be selectable as a Tab 2 preset target (like "Similar Literacy"), add it to the preset options list on the frontend — the backend `/api/v1/presets/closest` endpoint already works generically for any measure code, no backend change needed.

---

## Adding a new chart to Tab 2

1. Confirm which category (`demographics`/`economy`/`literacy`/`infrastructure`/`sanitation`/`drinking_water`) it belongs under — it should only render when that category is active in the sidebar filter.
2. Build it as its own component under `components/`, reading from the same `/api/v1/analytics` response already fetched for the tab — do not add a new API call per chart.
3. Use Recharts, and do not disable `isAnimationActive`; set `animationDuration` to match the platform-wide value used elsewhere (~500ms) so multiple charts feel synced.
4. Pull colors from `lib/stateColors.js` — never hardcode a hex value for a specific state.
5. If the metric needs comparison across wildly different scales (e.g. population), respect the per-capita/normalized toggle state (`DESIGN.md` §B.5) rather than always showing absolute values.

---

## Adding a new API endpoint

1. Ask first: does this really need a new endpoint, or does `/api/v1/analytics` already cover it with different query parameters? Most new data needs should extend the existing flexible endpoint, not spawn a new one (`ARCHITECTURE.md` §2).
2. If a new endpoint is genuinely needed (e.g. a new preset type), add it to the relevant router file under `app/routers/`, with a Pydantic response schema in `schemas.py` — never return a raw SQLAlchemy model.
3. Test it via `/docs` before writing any frontend code against it.
4. Document it in `API.md` with the same structure used for existing endpoints (params table, response example, behavior notes, error cases).

---

## Adding a database migration

1. Make the model change in `models.py` first.
2. Run `alembic revision --autogenerate -m "short description"`.
3. **Read the generated migration file** — autogenerate is a starting point, not guaranteed correct, especially for constraint changes.
4. Run `alembic upgrade head` locally and confirm the app still starts and existing queries still work before committing.
5. Never hand-edit the schema outside of a migration file.

---

## Adding a new Tab 2 preset type

1. Decide: is it a numeric "closest value" preset (like literacy/population) or a structural lookup (like neighbor)?
2. **Numeric presets** need no new endpoint — `/api/v1/presets/closest?metric=<new_measure_code>` already works generically.
3. **Structural presets** (anything not expressible as "closest value on measure X") need a new endpoint following the pattern in `presets.py` — always resolving to exactly one result (per the fixed two-state model), always excluding the anchor itself, always handling the "no valid match" case explicitly (return a null `state_code`, not a 500 error) rather than assuming a match always exists.
4. Add the disabled-state UX for any anchor where the preset can't resolve (see `DESIGN.md` §B.3's island-state handling as the reference pattern) — don't let a preset button silently do nothing on click.

---

## Working with the map component

1. `MapView` is one component with two rendering modes (full choropleth vs. two-state highlight) — see `ARCHITECTURE.md` §4. Before building a new map-related feature, check whether it belongs as a new mode/prop on `MapView` rather than a new component.
2. Never fetch or process boundary GeoJSON at request time — it's preprocessed offline into simplified/full-detail static files (`DATABASE.md` §6). If a new zoom level or view needs different detail, that's a new offline preprocessing step, not a runtime computation.

---

## General checks before considering any feature "done"

- Does it respect the fixed two-state model in Tab 2, or the click-only (no hover) model in Tab 1?
- Does it use `lib/stateColors.js` for any state-specific color?
- Does it go through React Query rather than raw `useEffect`/`useState` fetching?
- If it touches a measure, is `higher_is_better` set correctly?
- Is it covered in `/docs` (backend) or manually clicked through (frontend) before being called complete?
