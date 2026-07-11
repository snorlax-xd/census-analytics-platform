# DESIGN.md

Full UX/interaction specification for both tabs, consolidated from the original per-tab design discussions. This is the authoritative reference for *how the product behaves* — `ARCHITECTURE.md` and `API.md` cover how it's built underneath.

---

## Part A — Tab 1: National Map Explorer

### A.1 Overview

A single continuous, interactive map of India (all states and UTs) that:
- Colors every state by a selected metric (choropleth), with the metric's value labeled directly on the state.
- On click/tap, opens a focused single-state view in the foreground, with the national map dimmed behind it.
- Has a minimize control to return to the national view.

Interaction is deliberately limited to two mechanisms: **metric selection** and **click**. There is no hover-based preview layer and no dropdown-based state picker.

### A.2 Metric selector
- A button group/select above the map: population, sex ratio, literacy rate (extensible). `population_density` is removed from v1 because the primary dataset has no density or area column; add it later only if a supplementary 2011-era state/UT area table is sourced.
- Changing it recolors every state, updates each state's on-map label to that metric's value, and updates the legend's buckets/range.
- This is the only mechanism for previewing data at the national level — no separate hover tooltip exists.

### A.3 Click → focused state view
- Identical behavior on desktop and mobile — no hover dependency anywhere.
- Real, addressable route: `/tab1/state/:id` — not a client-side-only modal. Browser back/forward and refresh must work correctly.
- Enlarged single-state map in the foreground; national map dimmed/blurred behind.
- Stats panel shows the state's full metric set, with the currently-active metric (from the selector) shown first/emphasized, followed by the rest.
- Minimize returns to `/tab1`.

### A.4 Map rendering
- Boundary data from official Indian sources only (Census of India GIS / Survey of India) — never mixed with third-party GeoJSON packages, to avoid border mismatches.
- **Boundary vintage: 2011-era state/UT boundaries (35 regions), matching the primary data source exactly** — not the current 36-region map. The source dataset predates Telangana's creation, the J&K/Ladakh split, and the Dadra & Nagar Haveli/Daman & Diu merger, so the map must render undivided Andhra Pradesh, undivided Jammu & Kashmir, and a single combined Dadra & Nagar Haveli and Daman & Diu region. See `DATABASE.md` §2 for the full reasoning. This should be stated on-screen alongside the "Data as of Census 2011" label (§A.8) as one coherent vintage caveat, not two separate ones.
- Two boundary detail levels: simplified (national view) and full-detail (focused view), precomputed offline via `mapshaper` — never computed live.
- Pan and zoom (scroll+drag on desktop, pinch+drag on touch) is the **primary mechanism** for reaching small/clustered states — not permanent inset panels.

### A.5 Handling small and clustered states/UTs
- **Rejected approach:** permanent inset boxes for the North-East cluster plus leader-line callouts for isolated small states (Goa, Delhi, Chandigarh, Puducherry, Dadra & Nagar Haveli and Daman & Diu) all shown simultaneously — judged too visually busy, and an unnecessary constraint borrowed from print cartography (which can't zoom).
- **Adopted approach:** users reach any region via pan/zoom; as a state grows on screen its click target and label both become viable with no extra UI. **Quick-zoom shortcut chips** (e.g. "Northeast," "Delhi NCR") smoothly pan/zoom the camera on tap — optional convenience, not the only way in.
- **One fixed exception:** Andaman & Nicobar and Lakshadweep get a permanent small inset box in a map corner, at every zoom level, because their physical distance from the mainland can't be solved by zooming without wasting most of the canvas on empty ocean. This is standard convention on essentially every map of India and is a fixed requirement, not a fallback.

### A.6 State labeling — three-tier cascade
Evaluated **at render time** against the actual rendered bounding box at the current zoom/viewport (not hardcoded per state, since the same state may fit differently on mobile vs. desktop):
1. **Full state name** if it fits at a legible size.
2. **ISO 3166-2:IN code** (e.g. `MH`, `GJ`) if the name doesn't fit — standardized codes guarantee uniqueness, unlike invented abbreviations.
3. **Leader-line callout** if even the code doesn't fit — routed to a fixed set of "safe margin" slots around the map edge, assigned by nearest-available-slot to avoid collisions between multiple leader lines.
- **Font-size floor** (~9–10px): text is never shrunk smaller to force a fit; falls to the next tier instead.
- With pan/zoom now handling most small-state cases (§A.5), leader lines are a rare fallback, not a common default.
- **Implementation note (from the coding plan):** ship v1 with ISO codes only on every state to get the map working end-to-end; add the full three-tier cascade as a refinement pass afterward rather than blocking the first working map on exact text-fitting logic.

### A.7 Choropleth coloring
- Quantile or natural-breaks (Jenks) scale — **not** linear, since population-type data is heavily right-skewed (e.g. Uttar Pradesh/Bihar vs. the rest would otherwise flatten the whole map).
- Legend shows 5–6 discrete buckets with value ranges, updating whenever the metric selector changes.

### A.8 Data vintage
- All current data is Census 2011 only; multi-year comparison is deferred.
- A persistent "Data as of Census 2011" label is shown on the map view at all times — kept even at single-year scope so no retrofit is needed later.

### A.9 Explicitly out of scope for now
- Accessibility (colorblind-safe palette, keyboard nav, screen reader support) — backlog item, not abandoned.
- Multi-year census analysis.
- Hover-based preview layer.
- Dropdown/search as the fix for the small-state click-target problem (replaced by §A.5).

---

## Part B — Tab 2: State Comparison Engine

### B.1 Overview

Answers "give me everything about these two states, side by side" — deliberately narrower than Tab 1's "how does one state rank against all others" job. **Fixed at exactly two states, State A and State B** — not a variable-length list. This single simplification removed most of the interaction complexity that earlier, more open-ended drafts ran into (cap enforcement, multi-state tie-breaking, history-stack undo).

### B.2 Selection mechanism
- Two persistent, always-present selector slots (not a growing chip list). Each is a searchable combobox across all states/UTs, showing the ISO code as a prefix (e.g. `[MH] Maharashtra`), consistent with Tab 1's labeling.
- Clicking a filled slot reopens the combobox to change it — no separate "remove" affordance needed, since a slot is always either filled or being changed, never empty.
- **Swap** control exchanges State A and State B — unambiguous with exactly two fixed positions.
- Selection is encoded in the URL (`/tab2/compare?a=MH&b=GJ`) for shareability.

### B.3 Presets
Available presets for v1: **Neighboring State**, **Similar Literacy**, **Similar Population**. ("Similar GDP" and "Top Performers" deferred until economic metrics are confirmed in the v1 measure list.)

- **Resolution:** each preset fills only **State B**. Numeric presets (literacy, population) find the single closest state by absolute value difference — no ranking/slicing needed since only one match is required. "Neighboring State" looks up the static adjacency table, picking the neighbor with the longest shared border if there are several.
- **Disabled until State A is set** (tooltip: "Select a state first").
- **Island states as State A:** the "Neighboring State" preset is disabled specifically for these (tooltip: "No neighboring state available") since they have no land border — numeric presets remain available regardless.
- **Self-exclusion:** a state is never suggested as "closest to itself."
- **Missing data:** a state with no recorded value for a given metric is excluded from that preset's candidate pool, not treated as a zero value.
- **Undo:** since a preset only ever overwrites State B, undo is a single cached `previousStateB` value (not a history stack). A toast ("Replaced comparison state — Undo," ~6s) restores it if clicked.

### B.4 National average overlay
- **Not a third selectable state.** A toggle overlays a reference line/row for the national average on top of whatever A/B are selected — does not consume a slot, is not subject to the two-state cap.

### B.5 Visualization layout
- **Category sidebar**, flat (not nested): Demographics, Economy, Literacy, Infrastructure, Sanitation, Drinking Water — six categories, finalized in `DATABASE.md` §8. `Health` was dropped (no supporting data in the primary source); sanitation and drinking water were split out as their own dedicated categories rather than folded into `Infrastructure`, since the source data is granular enough on both (multiple latrine/bathing-facility types, multiple water-source types) to warrant separate treatment. Selecting a category filters which chart panels are shown.
- **Summary scorecard** (always shown first, above any chart): Metric | State A value | State B value | Difference, with a colored delta indicator (▲/▼). Missing data shown as "N/A," never as a blank or zero.
- **Diverging bar chart:** one metric at a time, State A/B as opposing bars from a shared center axis.
- **Radar chart:** normalized composite view of multiple indicators. Normalization method: **min-max scaling computed across all states/UTs** (not just A and B), so the shape reflects national standing, not just relative standing between the two chosen states.
- **Mini map:** reuses Tab 1's map component in a "highlight two states" mode (see `ARCHITECTURE.md` §4) rather than a separate map implementation.
- **Per-capita/normalized toggle:** required, not optional — comparing e.g. Sikkim and Uttar Pradesh on absolute values without this is close to meaningless.
- **Data vintage label:** same "Data as of Census 2011" label as Tab 1, for consistency.

### B.6 Wow-factor additions (Phase 1, in scope)

**B.6.1 Head-to-head verdict card**
- Shown above the scorecard: *"{State A} leads in {count} of {total} metrics. {State B} leads in {metric names}."* Omit a sentence if a state leads in zero metrics; ties are excluded from the count.
- **Requires the `higher_is_better` field** on every measure (see `DATABASE.md`) — only measures with a non-null value are counted, since "leading" is meaningless for a purely descriptive metric like raw population.
- Pure frontend computation over data already fetched for the scorecard — no new backend endpoint.

**B.6.2 National ranking badges**
- A badge ("Top 3 nationally") next to a metric row when that state ranks in the national top 3 (or bottom 3, for lower-is-better metrics).
- Only shown for directional metrics (same `higher_is_better` flag). Non-directional metrics like population should use neutral phrasing/styling if badged at all, not the same "achievement" visual treatment.
- Backend: `include_rank=true` on `/api/v1/analytics`, computed via a `RANK() OVER (PARTITION BY measure_id, year ORDER BY value DESC)` window function, inline at query time (cheap enough at 35 locales, the 2011-era count — no caching needed for v1).

**B.6.3 Chart entrance animations**
- Recharts animates by default — this is mostly a matter of not disabling `isAnimationActive`, plus setting an explicit consistent `animationDuration` (~500ms, ease-out) across all charts so they feel synced when several update together (e.g. after a swap).

**B.6.4 Consistent color language across tabs**
- **Each state gets one fixed color across the whole platform**, independent of whichever metric Tab 1's choropleth happens to be colored by at any moment. Implemented as a single shared module (`lib/stateColors.js`, see `ARCHITECTURE.md` §6) used by both tabs' bars, radar lines, badges, and highlight/selection states.

### B.7 Explicitly deferred to Phase 2
- Trend/small-multiples charts requiring multi-year data (not available yet).
- "Similar GDP" and "Top Performers" presets (pending confirmed economic metrics).
- 3+ state comparison (backend already supports it via the state-list parameter; only the frontend UI is deferred).
- Shareable comparison image export (`html2canvas`-based) — real implementation weight, worth a dedicated pass rather than folding into Phase 1.

---

## Part C — Shared conventions across both tabs

- **ISO 3166-2:IN codes** are the single standard used for labeling, chip prefixes, and API parameters — never invent separate abbreviations.
- **Data vintage labeling** ("Data as of Census 2011") appears identically on both tabs.
- **State color identity** (`lib/stateColors.js`) is shared, not duplicated or recomputed per tab.
- **Map rendering** is one component (`MapView`) used in two modes, not two separate implementations.
