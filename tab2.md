# Tab 2: State Comparison Engine — Specification

Census Analytics Platform — Tab 2 covers the fixed two-state comparison view: selection, presets, and the full visualization layout. This document captures the complete decided structure, including the reasoning behind each decision and how it ties into the rest of the platform's architecture (the tall fact table schema, the single flexible analytics endpoint, RBAC, and TanStack Query caching already decided for the platform as a whole).

---

## 1. Overview

Tab 2 answers one specific question: **"give me everything about these two states, side by side."** It is deliberately narrower in scope than Tab 1 (which answers "how does one state rank against all others, on one metric"). The two tabs should not overlap in job — Tab 2 does not try to support scanning many states at once; that belongs to Tab 1's map.

Core simplification decided for this build: **the comparison is fixed at exactly two states — State A and State B.** No variable-length list, no chip removal, no anchor-reassignment logic. This removes the majority of the interaction complexity that showed up in earlier drafts (cap enforcement, tie-breaking across multiple secondary states, undo history stacks) without losing any comparison capability that actually belongs in this tab.

---

## 2. Why fixed at exactly two states

- **Presets become a single closest-match query** instead of a ranked, sliced list — removes an entire category of ambiguous tie-breaking decisions (see §4).
- **Radar charts stay readable.** Overlapping polygons past 2–3 states is a known radar chart weakness; capping at 2 avoids it entirely rather than working around it.
- **Swap has unambiguous meaning** (A ⇄ B) — it didn't have a clean meaning against a variable-length list.
- **Multi-state scanning (e.g., all North-East states at once) is relocated to Tab 1**, where a future "select multiple states on the map" feature is a more natural fit than forcing it into a pairwise comparison tool.

---

## 3. Selection mechanism

### 3.1 Two fixed slots, not chips
- Two persistent selector slots, **State A** and **State B**, always present — not a dynamically growing chip list.
- Each slot is a searchable combobox (type-to-filter across all states/UTs), showing the ISO 3166-2:IN code as a prefix for consistency with Tab 1's labeling convention (e.g. `[MH] Maharashtra`).
- Clicking a filled slot reopens the combobox to change that state — no separate "remove" (×) affordance is needed, since a slot can never be empty once both are set, only replaced.

### 3.2 Swap
- A swap control between the two slots exchanges State A and State B instantly. No ambiguity here since there are always exactly two positions.

### 3.3 Shareable URL
- Selection is encoded in the URL: `/tab2/compare?a=MH&b=GJ`.
- The backend query parameter shape is **not** hardcoded to exactly two states (see §8) even though the frontend only ever sends two — this keeps a future 3+ state comparison a frontend-only change if ever revisited, without an API rewrite.

---

## 4. Presets

### 4.1 Presets for v1
- **Neighboring State** — fills State B with a state that shares a land border with State A.
- **Similar Literacy** — fills State B with the state whose literacy rate is numerically closest to State A's.
- **Similar Population** — fills State B with the state whose population is numerically closest to State A's.

("Top Performers" and "Similar GDP" from the earlier reference design are deferred — GDP-type economic metrics aren't confirmed as part of the v1 metric list yet; add back once that data is available.)

### 4.2 Resolution logic
- **Numeric presets (literacy, population, etc.):** a single SQL query — order all other states/UTs by absolute difference from State A's value on that metric, exclude State A itself, take the top 1. No slicing, no cap logic, no population-based tie-breaking — the "closest" state is simply whichever one is closest, full stop.
- **Neighboring State:** resolved via a static state-adjacency lookup table (which states share a border with which), not computed geometrically at request time. If State A has multiple neighbors, pick the one with the **longest shared border** — a defined, non-arbitrary rule, rather than an unrelated metric like population.

### 4.3 Edge cases
- **Presets are disabled until State A is set.** Greyed out with a tooltip: "Select a state first."
- **Island states with no land border** (Andaman & Nicobar, Lakshadweep) as State A: the "Neighboring State" preset is disabled specifically for these, with its own tooltip: "No neighboring state available." It does not silently fail or fall back to an unrelated behavior — the numeric presets (literacy, population) remain available for these states regardless, since those don't depend on adjacency.
- **Self-exclusion:** all preset queries explicitly exclude State A from their own result set (a state is never "closest to itself").
- **Missing metric data:** if a state has no value for a given metric (some UTs lack certain administrative-level statistics), it is excluded from that specific preset's candidate pool rather than treated as a value of zero, which would otherwise distort "closest" results.

### 4.4 Undo
- Since a preset only ever overwrites **State B** (never State A), undo is a single cached value, not a history stack: `previousStateB`. Clicking a preset caches the current State B before replacing it.
- A toast appears bottom-center: "Replaced comparison state — Undo," visible for ~6 seconds, restoring the cached value if clicked. This remains useful even in the simplified model, since a preset can still overwrite a State B the user picked manually.

---

## 5. National average overlay

- **Not a third selectable state.** A toggle ("Show national average") overlays a reference line/row on top of whatever State A/State B are currently selected — it does not consume a slot and is not part of the 2-state cap.
- Computed as an aggregate across all states/UTs for each metric, refreshed whenever the underlying dataset updates (see §10.3 on caching).

---

## 6. Visualization layout

Reference design (the dark-mode dashboard mockup) is the visual direction to build toward — sidebar category navigation, summary scorecard, and a grid of chart panels. A few structural adjustments from that reference are decided below.

### 6.1 Category grouping — flattened
- The reference design's sidebar had inconsistent nested categories (e.g. "Literacy" containing sub-items also called "Demographics" and "Literacy"). This is corrected to a **single flat level**: Demographics, Economy, Literacy, Health, Infrastructure — no nested nav nesting. Selecting a category filters which chart panels are shown below; no multi-level tree to build or maintain.

### 6.2 Summary scorecard
- A table: Metric | State A value | State B value | Difference — always the first thing shown, before any chart.
- Difference shown with a colored delta indicator (e.g. green ▲ / red ▼) relative to State A.
- Rows where either state has missing data show "N/A" rather than a blank cell or a zero, so it can't be misread as an actual value of zero.

### 6.3 Diverging bar chart
- One metric at a time, State A and State B as opposing bars from a shared center axis. Good for single-metric "who's ahead and by how much" reads. Used for the currently-selected category's headline metric.

### 6.4 Radar chart
- Multi-metric composite view of normalized indicators (e.g. literacy, sex ratio, health, infrastructure) across State A vs State B — clean at exactly two states, since we're not fighting radar-chart overlap issues.
- **Normalization method: min-max scaling**, computed across *all* states/UTs (not just A and B), so the radar reflects each state's national standing, not just their standing relative to each other. This must be decided and documented, since different normalization methods produce visually different — and equally "correct-looking" — radar shapes.

### 6.5 Mini map
- A small India outline with State A and State B highlighted, reusing Tab 1's existing map rendering component (same boundary data, same simplified geometry) rather than building a second map implementation. This is a straightforward reuse, not new engineering.

### 6.6 Per-capita / normalized toggle
- A toggle for switching between absolute values and population-adjusted (per-capita or per-1000) values. Necessary because comparing, say, Sikkim and Uttar Pradesh on absolute population-scale metrics is close to meaningless without this — this was flagged as an open risk earlier and is resolved here as a required toggle, not optional polish.

### 6.7 Data vintage
- The same persistent "Data as of Census 2011" label used in Tab 1 appears here too, for consistency and to avoid re-explaining data vintage per tab.

### 6.8 Wow-factor additions (Phase 1)

These layer on top of the structure above without touching the fixed two-state selection, presets, or backend query shape already decided. All four are in scope for Phase 1 given how little they add to the existing build.

**6.8.1 Head-to-head verdict card**
- Positioned above the summary scorecard, before any chart.
- Template: *"{State A} leads in {count} of {total} metrics. {State B} leads in {metric names}."* If one state leads in zero metrics, omit that sentence rather than showing "leads in 0 metrics." Tied values are excluded from the count and don't need their own callout.
- **Requires a directionality flag per metric.** Not every metric has a "better" direction — population and area are purely descriptive, while literacy rate (higher is better) and infant mortality (lower is better) do. Add a `higher_is_better` field (nullable — `null` for non-directional metrics) to the measure vocabulary, and only include metrics with a non-null value in the verdict's win-count. This prevents a misleading claim like "Maharashtra leads" on a metric where "leading" has no real meaning.
- **Implementation is pure frontend computation** — a single reduce over the comparison data you've already fetched for the scorecard. No new backend endpoint needed.

**6.8.2 National ranking badges**
- A small badge next to a metric row when that state's value ranks in the **national top 3** for that metric (or bottom 3, for metrics where lower is better) — e.g. "Top 3 nationally." Cap at top 3 to avoid badge overload; don't show a badge for every mid-table rank.
- Only shown for **directional** metrics (reusing the same `higher_is_better` flag from 6.8.1) — a badge like "Top 3 nationally" implies achievement, which doesn't make sense for a purely descriptive metric like raw population. If you want to badge population too, use neutral phrasing/color ("largest population" in a neutral tone) rather than the same "achievement" styling used for literacy or health metrics.
- **Backend**: extend the existing analytics endpoint response with an optional rank field per metric per state — `GET /api/v1/analytics?states=MH,GJ&year=2011&metrics=all&include_rank=true`. Compute via a single SQL window function, `RANK() OVER (PARTITION BY metric_id, year ORDER BY value DESC)`, run inline at query time — with only 36 states/UTs this is cheap enough that no caching or materialization is needed for v1.

**6.8.3 Chart entrance animations**
- Applies to the diverging bar chart and radar chart. Recharts animates by default — this is largely a matter of **not disabling** `isAnimationActive`, not adding new code.
- Set an explicit, consistent `animationDuration` (e.g. 500ms, ease-out) on every chart rather than relying on each chart type's own default duration — this keeps multiple charts feeling synced when they update together, e.g. right after a state swap or preset selection.
- No new dependency required — this is entirely inside Recharts' existing API.

**6.8.4 Consistent color language across tabs**
- **Decision: each state gets one fixed color across the whole platform**, independent of whatever metric Tab 1's choropleth happens to be colored by at any given moment. Maharashtra is always the same shade everywhere it appears — Tab 1 highlight, Tab 2 bars, Tab 2 radar, badges. This keeps a clean "State A is always this color" mental model, and decouples Tab 2's visuals from Tab 1's metric-selector state.
- **Implementation**: a single shared module (e.g. `stateColors.ts`) exporting a `{ [stateCode]: hexColor }` map, either curated by hand for a fixed palette of distinct colors or generated deterministically from the state code. Imported by both tabs — Tab 1 uses it only for selection/highlight (its choropleth itself stays metric-driven, per §6.6 of the Tab 1 spec), Tab 2 uses it as the default series color for every chart and badge.

---

## 7. Explicitly deferred to Phase 2

- **Trend / small-multiples charts** (e.g. "Population Density Trend 2001–2011") from the original reference design — these require multi-year data, which doesn't exist yet since the platform is currently scoped to Census 2011 only (per the Tab 1 decision). Do not attempt to fake a trend line from a single data point.
- **"Similar GDP" and "Top Performers" presets** — deferred until the underlying economic metrics are confirmed as part of the v1 dataset.
- **3+ state comparison** — not building this now, but the backend query shape (§8) is deliberately kept list-based so this is a frontend-only addition later, not an API rewrite.

---

## 8. Backend

### 8.1 Reuse the platform's single flexible analytics endpoint
- Tab 2 does **not** get a bespoke `/compare` endpoint. It calls the same general-purpose analytics endpoint already decided for the platform, parameterized with a list of locale codes and a year:
  `GET /api/v1/analytics?states=MH,GJ&year=2011&metrics=all`
- Even though the frontend only ever sends exactly two state codes right now, the endpoint itself accepts an arbitrary-length list — this is what keeps a future multi-state comparison a frontend change only.

### 8.2 Preset resolution as a separate, small endpoint
- `GET /api/v1/presets/closest?anchor=MH&metric=literacy_rate&year=2011` → returns a single closest state code, using the `ORDER BY ABS(value - anchor_value) LIMIT 1` pattern from §4.2.
- `GET /api/v1/presets/neighbor?anchor=MH` → returns a single neighboring state code from the static adjacency table, or a 204/empty response for island states (frontend interprets this as "disable the preset," not an error).

### 8.3 RBAC
- Both endpoints are **public read-only** — no authentication required, consistent with the decision that Tab 1 and Tab 2 are open data views. RBAC only gates the data-curation/admin side of the platform (uploading new census data, publishing new measure versions), not the comparison views themselves.

---

## 9. Database

- Reuses the platform's existing **tall/long fact table schema** (one row per locale × metric × year) — no new tables needed for the comparison feature itself, just filtered queries against the existing structure.
- The **static state-adjacency table** (for the "Neighboring State" preset) is a new, small, mostly-static reference table: `state_adjacency(state_code, neighbor_code, shared_border_length)` — populated once from official boundary data, not derived at query time.
- **Indexing note:** the "closest value" preset query benefits from an index on `(metric_id, year, value)` in the fact table, since it's effectively a nearest-neighbor sort on `value` filtered by metric and year — worth adding if this query is used frequently.

---

## 10. Frontend architecture

### 10.1 State management — intentionally simple
- No anchor-tracking state machine, no history stack array. Just:
  - `stateA`, `stateB` (the two selected locale codes)
  - `previousStateB` (single cached value, for undo)
  - `showNationalAverage` (boolean)
  - `perCapitaMode` (boolean)
  - `activeCategory` (which metric category is currently filtering the chart panels)
- This is a handful of `useState` values, not a custom state manager class — appropriate for the fixed two-slot model.

### 10.2 Component breakdown
- `StateSelector` (×2 — State A, State B combobox)
- `SwapButton`
- `PresetRow` (disabled/enabled based on whether State A is set, and per-preset based on data availability)
- `UndoToast`
- `ScorecardTable`
- `DivergingBarChart`, `RadarChart` — reused per active category
- `ComparisonMiniMap` (imports Tab 1's map component)
- `CategorySidebar` (flat list, per §6.1)

### 10.3 Caching
- Uses the platform's existing TanStack Query setup for fetching and cache invalidation, consistent with the rest of the platform — no separate caching strategy introduced for this tab.

---

## 11. Open items for next pass

- Confirm the full v1 metric list per category (Demographics, Economy, Literacy, Health, Infrastructure) so the scorecard and category filtering have a finalized field list.
- Decide the exact color ramp/style for the diverging bar chart and radar chart, consistent with Tab 1's chosen palette.
- Confirm whether the national average overlay should be on by default or opt-in via the toggle.
