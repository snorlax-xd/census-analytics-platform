# PHASE4_5_STABILIZATION_PROMPT_SEQUENCE.md

A short stabilization pass between Phase 4 (Tab 1) and Phase 5 (Tab 2),
addressing the findings in `TAB1_AUDIT_FINDINGS.md`. Same rules as
`PHASE4_PROMPT_SEQUENCE.md`: send one prompt at a time, verify (eyeball
it yourself where visual), commit before moving to the next prompt.

**Why this exists as its own phase instead of folding into Phase 6
polish:** `ARCHITECTURE.md` §4/§6 establish `MapView`, `stateColors.js`,
and the general visual language as *shared* between both tabs. Two of
these fixes (category-name formatting, design tokens) are things Tab 2
needs identically per `DESIGN.md` §B.5. Fixing them now means Tab 2
inherits the fix for free; fixing them after Tab 2 exists means fixing
them twice, in two places, possibly having diverged. The StateDetail
layout bug is also severe enough (doesn't implement the spec at all,
not just imperfectly) that it shouldn't sit broken while a whole second
tab gets built next to it.

**Scope discipline:** this is a stabilization pass, not a redesign. Do
not restyle things that aren't in `TAB1_AUDIT_FINDINGS.md`. Do not touch
the boundary/winding pipeline (`prepare_boundaries.py`,
`fix_winding_post_mapshaper.py`, `rebuild_boundaries.ps1`) — that's
solved and out of scope here. Do not implement the full three-tier label
cascade — still correctly deferred per `DESIGN.md` §A.6.

---

### Prompt 1 — Diagnose the negative-percentage bug (investigate only)

```
Stabilization step 1 only: investigate BUG-2 from TAB1_AUDIT_FINDINGS.md
— the "Households With TV: -4.13%" value shown on the Uttar Pradesh
focused view. Do not fix anything yet. Trace the exact measure_code this
value comes from in the API response for states=UP, and check two
things: (a) is the frontend rendering the correct field for this row's
label, and (b) does the raw india-districts-census-2011.csv, aggregated
the same way ROADMAP.md Phase 1 describes, actually produce a negative
value for this measure in Uttar Pradesh. Report which of the two it is
— a frontend field-mapping bug or a backend aggregation bug — with the
exact evidence (API response snippet or CSV recomputation), before any
code changes.
```
**Verify:** read the diagnosis, confirm it identifies a specific root
cause with evidence, not a guess. Do not proceed to Prompt 2 until this
is resolved — Prompt 2 needs to know whether the fix belongs in the
frontend or the backend.

---

### Prompt 2 — Fix the negative-percentage bug

```
Stabilization step 2 only: fix the root cause identified in step 1,
in whichever single file it actually lives (frontend field mapping or
backend seed/aggregation logic — not both speculatively). Do not touch
unrelated measures or files. Re-verify against the live API response
for Uttar Pradesh and confirm the value is no longer negative and looks
plausible against the raw CSV.
```
**Verify:** `/tab1/state/UP`'s stats panel no longer shows an impossible
value for this measure; spot-check one or two other states' values for
the same measure look sane too. Commit.

---

### Prompt 3 — Shared category/measure display-name formatter (DS-1)

```
Stabilization step 3 only: create a single shared formatter — e.g.
Frontend/src/lib/formatMeasure.ts — that maps internal category codes
(demographics, economy, literacy, infrastructure, sanitation,
drinking_water) to the display names DESIGN.md §B.5 already defines
(Demographics, Economy, Literacy, Infrastructure, Sanitation, Drinking
Water), and maps measure_code/measure_name to clean display text
generally (title-casing, no raw snake_case ever shown to the user).
Apply it only in Tab 1's StateDetail stats panel for now — do not build
Tab 2 components yet. This fixes BUG-3 and lays the groundwork DS-1
flags as needed by Tab 2 later.
```
**Verify:** StateDetail no longer shows raw slugs like
`sanitation_drinking_water` anywhere. Commit.

---

### Prompt 4 — Rebuild StateDetail to actually match DESIGN.md §A.3

```
Stabilization step 4 only: rebuild StateDetail.tsx to implement
DESIGN.md §A.3 as written, not the current two-card side-by-side layout
(BUG-1). Required: the enlarged single-state map renders in the
foreground; the national map (MapView in its existing national mode)
renders behind it, visibly dimmed/blurred, not hidden; the stats panel
uses the step-3 formatter for all labels; the currently-active metric
(from Tab 1's selector, passed via the existing ?metric= URL param)
stays visually emphasized first, per the existing behavior — don't
regress that part, it already works. Minimize control still returns to
/tab1. Do not add new data fetching — this is a layout/composition fix
using data and endpoints that already work.
```
**Verify:** click into any state from `/tab1`; confirm you can see the
dimmed national map behind the enlarged focused state, not a plain white
two-card page. Confirm minimize and browser back/forward still work
(per the original Phase 4 Prompt 5 requirement — don't regress that).
Commit.

---

### Prompt 5 — Islands inset: size, clarity, and the overlap bug

```
Stabilization step 5 only: fix BUG-4 and BUG-5 together, since they're
the same component. Increase the islands inset's rendered size enough
that Andaman & Nicobar and Lakshadweep are recognizable shapes, not
dots — adjust the inset's internal MapView instance's projection/scale,
not the main map's. Fix the z-index/positioning so the inset box never
overlaps or obscures a state label on the main map, at any zoom level or
quick-zoom shortcut (reproduce the Delhi NCR quick-zoom case specifically
and confirm the "UP" label is no longer hidden behind it). Do not change
the fixed-corner-inset approach itself — that's a deliberate DESIGN.md
§A.5 decision, not open for revision here.
```
**Verify:** islands are legible and clickable into their own focused
view; overlap with Delhi NCR / any other quick-zoom label no longer
happens. Commit.

---

### Prompt 6 — Northeast label collision (UX-1)

```
Stabilization step 6 only: fix the label collision in the Northeast
cluster (SK, AR, AS, ML, NL, TR, MZ, MN overlapping at default zoom).
This is NOT step 3 of the three-tier cascade from DESIGN.md §A.6 — do
not implement leader-line callouts or name-fitting logic. Stay within
ISO-codes-only for v1, exactly as already shipped. The fix here is
narrower: basic overlap avoidance for the existing code labels only
(e.g. skip rendering a label if its bounding box would collide with an
already-placed one at the current zoom, matching the "never force an
illegible fit" principle already established for the font-size floor).
```
**Verify:** at default national zoom, Northeast cluster labels no longer
overlap each other; zooming in via the "Northeast" quick-zoom chip still
reveals all of them once there's room. Commit.

---

### Prompt 7 — Shared design tokens + apply them (DS-2, UX-3, UX-4, UX-5, UX-6)

```
Stabilization step 7 only: establish a small shared set of design
tokens in the existing Tailwind config (spacing scale, a typography
scale with at least 3 weights/sizes beyond the default, and a subtle
elevation/shadow scale for card-like surfaces) and apply them across
Tab 1's existing components: the metric selector, quick-zoom chips, the
legend, and StateDetail's stats panel. Specifically:
- Group StateDetail's metric rows by category (using the step-3
  formatter), with visual separation between category groups, so it
  reads as organized data rather than a flat list (UX-3).
- Give the legend's buckets clearer spacing so value ranges are easy to
  read at a glance (UX-4).
- Give the metric selector and quick-zoom chips distinct visual
  treatment from each other so their different purposes are clear at a
  glance (UX-5) — do not change their functional behavior.
- Add a subtle hover affordance on clickable states (cursor + outline
  only, no data preview, per DESIGN.md §A.2/§A.9's explicit ban on a
  hover preview layer) (UX-2).
Do not redesign colors, layout structure, or add any new pages/routes —
this is a token-and-consistency pass over what already exists.
```
**Verify:** do a visual pass across `/tab1`, all three metrics, a
focused state view, and both quick-zoom shortcuts. Confirm nothing
functional changed, only visual polish and the grouping/hover additions
described. Commit.

---

## After Prompt 7

Do a final manual click-through against `DESIGN.md` Part A as a
checklist, same as Phase 4's own closing step. Once that's clean, proceed
to Phase 5 (`ROADMAP.md`) — Tab 2 — which now inherits the category
formatter (DS-1) and design tokens (DS-2) this phase built, rather than
needing to invent its own versions of either.
