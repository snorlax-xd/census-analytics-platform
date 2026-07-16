# PHASE5_TAB2_PROMPT_SEQUENCE.md

Tab 2 broken into small, sequential Codex prompts, same discipline as
`PHASE4_PROMPT_SEQUENCE.md`: **one prompt at a time, verify visually,
commit before the next one.** Phase 4.5 showed what happens when this
gets skipped (prompts 4–6 got merged into one message) — it worked out,
but Tab 2 has more moving parts (charts, presets, two data sources) than
Tab 1's map did, so the margin for a merged-diff mistake is smaller.
Don't repeat that here.

**Prerequisite check before Prompt 1:** confirm
`PHASE4_5_STABILIZATION_ADDENDUM.md` Prompts 8–10 are done and verified
(dimmed background map visible, islands legible, tokens applied). Confirm
`lib/stateColors.js` exports all 35 state colors per `DESIGN_SYSTEM.md`
§5 — if it's still a stub, that's Prompt 0 below, not a mid-Phase-5
surprise.

**Backend note, confirmed from the earlier session:** `/api/v1/analytics`,
`/api/v1/presets/closest`, and `/api/v1/presets/neighbor` are already
built, seeded with real 2011 data, and were verified end-to-end
(including `state_adjacency` with 126 rows). **Phase 5 is frontend-only.**
No backend prompt is needed unless a genuine gap is discovered — if any
prompt below seems to need a backend change, stop and flag it before
writing backend code, per `API.md`'s "Not yet built" section and the
project's own "treat the backend API as stable" instruction.

---

### Prompt 0 (only if needed) — Confirm/complete lib/stateColors.js

```
Before any Tab 2 UI work: read Frontend/src/lib/stateColors.js. If it
already exports a function that returns a distinct, fixed color for
each of the 35 Census-2011 locale codes (reuse the same code list
already established in Frontend/src/lib/locales.ts), report that it's
ready and make no changes. If it's a stub or incomplete, implement it
now: one fixed hex color per state/UT code, visually distinct enough
that two adjacent bars/lines/badges are never confusable, exported as a
single function e.g. getStateColor(isoCode: string): string. Do not
build any Tab 2 UI in this step — this is a prerequisite check only.
```
**Verify:** confirm all 35 codes are covered, no two colors look
identical. Commit only if a change was made.

---

### Prompt 1 — Two state selectors, URL state, no data fetching yet

```
Phase 5, step 1 only: build the two persistent state-selector slots per
DESIGN.md §B.2. Each is a searchable combobox across all 35 states/UTs
(reuse Frontend/src/lib/locales.ts for the code/name list), displaying
each option as "[ISO] Full Name" (e.g. "[MH] Maharashtra"), consistent
with Tab 1's labeling convention. Both slots are always visible — never
an empty "add state" placeholder, and clicking a filled slot reopens the
combobox to change it. Selection state is encoded in the URL exactly as
/tab2/compare?a=MH&b=GJ, using react-router-dom's existing query-param
patterns from Tab 1's ?metric= usage. Do not add the swap control, any
presets, any data fetching, or any chart/scorecard rendering yet — this
step only gets both slots working and syncing to the URL.
```
**Verify:** picking a state in either slot updates the URL; loading
`/tab2/compare?a=MH&b=GJ` directly pre-fills both slots correctly
(confirms URL-as-source-of-truth, not just one-way sync). Commit.

---

### Prompt 2 — Swap control

```
Phase 5, step 2 only: add the Swap control per DESIGN.md §B.2 — a single
button that exchanges State A and State B, updating the URL
(?a=GJ&b=MH becomes ?a=MH... reversed) and both combobox displays. Do
not add anything else.
```
**Verify:** swap exchanges both slots and the URL correctly, repeatedly
(swap twice returns to the original state). Commit.

---

### Prompt 3 — Presets: Neighboring State, Similar Literacy, Similar Population

```
Phase 5, step 3 only: add the three preset buttons per DESIGN.md §B.3,
wired to the existing GET /api/v1/presets/neighbor and
GET /api/v1/presets/closest?metric=literacy_rate /
?metric=population endpoints (API.md — do not modify these endpoints).
Exact behavior required, all of it:
- Each preset fills only State B, never State A.
- All three are disabled with tooltip "Select a state first" until
  State A is set.
- "Neighboring State" is additionally disabled, with tooltip "No
  neighboring state available", specifically when State A is an island
  state with no land border — this comes from the API returning
  { state_code: null } for /presets/neighbor, per API.md's documented
  behavior; a null state_code is NOT an error response and must not be
  handled as one. The two numeric presets stay enabled regardless of
  whether State A is an island.
- A state is never suggested as "closest to itself" (verify this is
  true given the backend already excludes the anchor — do not
  duplicate that exclusion logic client-side, just don't break it by,
  e.g., re-adding the anchor to a candidate list).
- Undo: applying a preset caches the single previous State B value
  (not a history stack) before overwriting it. A toast reading
  "Replaced comparison state — Undo" appears for approximately 6
  seconds; clicking Undo restores the cached previous State B. A
  second preset click before the toast expires simply replaces the
  cached value with the new previous state — still only ever one level
  of undo, never a stack.
Do not add the scorecard, charts, or any other UI yet.
```
**Verify:** test all three presets with a normal state as State A, then
with Andaman & Nicobar as State A (confirm Neighboring State disables
with the correct tooltip while the other two stay active), then test
Undo actually restores the prior State B. Commit.

---

### Prompt 4 — Fetch analytics data for A+B, build the Summary Scorecard

```
Phase 5, step 4 only: once both State A and State B are set, fetch
their full metric sets via the existing GET /api/v1/analytics?states=A,B
endpoint (React Query, same caching pattern as Tab 1 — query key should
include both state codes so changing either triggers a refetch, per
ARCHITECTURE.md §5). Build the Summary Scorecard per DESIGN.md §B.5:
always shown first, above any chart. Columns: Metric | State A value |
State B value | Difference, with a colored ▲/▼ delta indicator.
Category names and measure names must come from
Frontend/src/lib/formatMeasure.ts (built in Phase 4.5) — never show raw
slugs. Missing data (a measure present for one state but not the other)
displays as "N/A" — never a blank cell or a zero. Add the flat category
sidebar per DESIGN.md §B.5's six categories (Demographics, Economy,
Literacy, Infrastructure, Sanitation, Drinking Water — from
formatMeasure.ts's existing mapping) that filters which scorecard rows
are shown; sidebar is flat, not nested. Add the "Data as of Census 2011"
label matching Tab 1's, per DESIGN.md Part C. Do not add any charts,
verdict card, badges, or toggles yet.
```
**Verify:** pick two states, confirm every measure appears with correct
A/B values, correct delta direction, N/A for any genuinely missing
measure (check a measure you know is sparse, if any exist — otherwise
confirm the N/A path doesn't false-trigger on complete data), and that
switching category sidebar filters the visible rows correctly. Commit.

---

### Prompt 5 — Diverging bar chart

```
Phase 5, step 5 only: add the diverging bar chart per DESIGN.md §B.5 —
one metric at a time, State A and State B as opposing bars from a
shared center axis, using Recharts. The active metric for this chart
should follow whichever scorecard row the user has most recently
interacted with, or default to the first metric in the currently
selected category — use your judgment on the exact selection mechanism
but keep it simple (e.g. clicking a scorecard row could set the chart's
active metric) rather than adding a whole new separate metric-picker
control that duplicates the scorecard. Use Frontend/src/lib/stateColors.js
for each state's bar color (per DESIGN_SYSTEM.md §5 — not colorScale.js,
that's Tab 1's choropleth-only module). Do not enable chart animation
tuning yet — that's a later step (DESIGN.md §B.6.3), plain Recharts
defaults are fine for now. Do not add the radar chart yet.
```
**Verify:** the bar chart updates correctly per metric, uses each
state's fixed color (matching what Tab 1 would eventually use for the
same state, once color identity is visible there too), and the two
bars diverge from a visibly shared center line. Commit.

---

### Prompt 6 — Radar chart with national min-max normalization

```
Phase 5, step 6 only: add the radar chart per DESIGN.md §B.5. This is
the one Tab 2 component that needs data beyond just States A and B:
normalization is min-max scaling computed across ALL 35 states/UTs, not
just the two selected — so the shape reflects national standing, not
just relative standing between the two chosen states. Fetch all-35-state
data the same way Tab 1's choropleth does (GET /api/v1/analytics with
all 35 codes) via React Query, so it benefits from the same cache if
Tab 1 has already fetched it in this session — do not write a second,
differently-shaped fetch for the same underlying data if you can share
the query key/shape. Compute min/max per measure across all 35 states
client-side, normalize State A and B's values against that range for
whichever indicators are shown on the radar (pick a sensible fixed set
of directional indicators for v1 — e.g. one or two per category with a
non-null higher_is_better — rather than trying to plot all ~32 measures
on one radar, which would be unreadable). Use stateColors.js for the two
radar lines' colors, consistent with the bar chart.
```
**Verify:** radar shape changes appropriately when swapping to a very
different pair of states (e.g. Kerala vs. Bihar should show a visibly
different radar shape than Punjab vs. Haryana). Confirm the two radar
line colors match the same states' bar chart colors from Prompt 5.
Commit.

---

### Prompt 7 — Mini map in highlight mode

```
Phase 5, step 7 only: extend the existing MapView component (do not
create a second map component, per ARCHITECTURE.md §4's "one map
implementation, two rendering modes" requirement) with a new "highlight
two states" mode for Tab 2's mini map: no choropleth coloring, just
outlines, with State A and State B filled/outlined using their
stateColors.js colors and every other state rendered neutral/muted. No
click-to-navigate behavior in this mode — Tab 2's map is a visual
reference, not a navigation control, unlike Tab 1's. Reuse whatever
hover-affordance convention DESIGN_SYSTEM.md §8 established, but only if
it makes sense for a non-clickable map — if there's nothing to click,
there's nothing to hover-affordance; use judgment, don't force it.
```
**Verify:** mini map shows only States A and B highlighted in their
correct fixed colors, everything else neutral, no stray click behavior.
Commit.

---

### Prompt 8 — National average overlay + per-capita/normalized toggle

```
Phase 5, step 8 only: add two toggles per DESIGN.md §B.4/§B.5.
1. National average overlay: NOT a third selectable state, does not
   consume a comparison slot. A toggle that overlays a reference
   line/row for the national average on top of the scorecard and/or
   diverging bar chart (your judgment on exactly where it's clearest —
   at minimum it must appear somewhere the person can see it against
   both A and B's values, not be a separate disconnected panel).
2. Per-capita/normalized toggle: required, not optional, shown
   whenever relevant absolute-value metrics are in view (DESIGN.md
   §B.5 calls this close to meaningless to omit for metrics like
   population where Sikkim vs. Uttar Pradesh absolute values are
   incomparable without it). Confirm which existing measures in the API
   response are raw counts vs. already-rate/percentage before deciding
   which rows this toggle actually affects — do not apply a
   normalization transform to a measure that's already a rate/percentage.
```
**Verify:** national average toggle shows a real, correct national
average value (computed from all-35-state data, not hardcoded); the
per-capita toggle only affects absolute-count measures and leaves
already-normalized ones (percentages, rates) untouched. Commit.

---

### Prompt 9 — Verdict card

```
Phase 5, step 9 only: add the head-to-head verdict card per DESIGN.md
§B.6.1, shown above the scorecard. Exact text pattern: "{State A} leads
in {count} of {total} metrics. {State B} leads in {metric names}."  Omit
either state's sentence entirely if that state leads in zero metrics —
do not print "leads in 0 metrics." Ties are excluded from both the count
and the total. Only measures with a non-null higher_is_better count at
all — a purely descriptive metric like raw population must not be
counted as either state "leading." This is pure frontend computation
over data already fetched for the scorecard in Prompt 4 — no new
backend endpoint, no new API call.
```
**Verify:** manually cross-check the verdict card's count against the
scorecard's own delta indicators for at least one state pair — the
numbers must agree. Test a pair where one state leads in zero
directional metrics, confirm that state's sentence is omitted, not
shown as "leads in 0." Commit.

---

### Prompt 10 — National ranking badges

```
Phase 5, step 10 only: add ranking badges per DESIGN.md §B.6.2. Fetch
with include_rank=true on the existing /api/v1/analytics call (already
supported by the backend, confirmed working — do not modify the
endpoint). Show a badge ("Top 3 nationally") next to a scorecard row
when that state ranks in the national top 3 for that measure — or
bottom 3, for measures where higher_is_better is false. Badges only
appear for directional metrics (non-null higher_is_better) — a
non-directional metric like raw population should either show no badge
or a visually neutral badge style, explicitly not the same
achievement-styled badge used for directional metrics.
```
**Verify:** confirm a state known to rank highly on a specific metric
(e.g. Kerala on literacy_rate) actually shows the badge; confirm
population never shows an achievement-styled badge. Commit.

---

### Prompt 11 — Chart animations + final shared-color consistency pass

```
Phase 5, step 11 only, and this is the last step: tune chart animations
per DESIGN.md §B.6.3 — confirm isAnimationActive is not disabled on any
Recharts instance from Prompts 5/6, and set an explicit, consistent
animationDuration of ~500ms with an ease-out curve across the diverging
bar chart and radar chart, so they feel synced when both update
together (e.g. immediately after a swap or preset application). As a
final consistency check, not a new feature: confirm every place a state
needs visual identity on this page — scorecard row highlights if any,
bar chart, radar chart, mini map, badges — uses the exact same
stateColors.js color for that state, with no component using a
different or recomputed color for the same state.
```
**Verify:** trigger a swap and visually confirm both charts animate in
sync rather than one lagging or snapping instantly. Do a final visual
sweep confirming color consistency for a given state across every
Tab 2 surface simultaneously. Commit.

---

## After Prompt 11

Phase 5 is done. Do the same closing move as Phase 4: a full manual
click-through against `DESIGN.md` Part B as a checklist — selectors,
swap, all three presets (including the island-state edge case), undo,
scorecard with N/A handling, both charts, mini map, both toggles,
verdict card, badges, animations — before telling Codex to proceed to
Phase 6 (Polish) per `ROADMAP.md`.
