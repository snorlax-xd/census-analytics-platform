# PHASE4_PROMPT_SEQUENCE.md

Tab 1 broken into small, sequential Codex prompts. Send one at a time. After each, verify (per `RUNBOOK.md` §5 — eyeball it yourself where visual) and **commit before moving to the next prompt**. This keeps every diff small, reviewable, and cheap to fix if something's off — a "build Tab 1" mega-prompt would burn far more tokens if any single part needs correction, since you'd be debugging inside a huge diff instead of a small one.

One prerequisite blocks Prompt 1 below: **boundary GeoJSON (2011-era, 35 regions) doesn't exist in the repo yet.** Sourcing and preprocessing this is not a good use of Codex's tokens — it's a one-time research/data task, not iterative coding. I can help find and prep this next, outside Codex, so Codex only has to consume a ready file. Flag this to me before running Prompt 1 if it's not sourced yet.

---

### Prompt 1 — Static map render

```
Phase 4, step 1 only: render the national map. Add the simplified India
boundary GeoJSON (already placed at [path]) to Frontend using
react-simple-maps per ARCHITECTURE.md. Build MapView.jsx to render all 35
states/UTs as static shapes, no coloring, no interaction yet — just the
outline rendering correctly on the /tab1 route, replacing the current
placeholder panel. Do not touch the backend. Stop here; do not add the
metric selector yet.
```
**Verify:** open `/tab1`, confirm the map outline renders correctly (all 35 regions visible, correct relative shapes). Commit.

---

### Prompt 2 — Metric selector + choropleth coloring

```
Phase 4, step 2 only: add the metric selector (population, sex ratio,
literacy rate — per DESIGN.md §A.2, population_density excluded per the
earlier decision) as a button group above the map. Wire it to the
existing /api/v1/analytics endpoint (do not modify the backend contract).
Color each state via a d3-scale quantile scale per DESIGN.md §A.7, and
add a legend that updates with the selected metric. Use lib/colorScale.js
for this, per ARCHITECTURE.md. Do not add pan/zoom or click behavior yet.
```
**Verify:** switch between metrics, confirm the map recolors and the legend updates correctly with real data. Commit.

---

### Prompt 3 — State labels (ISO codes only, v1 simplification)

```
Phase 4, step 3 only: label each state with its ISO code (per
tab1_national_map_explorer_spec.md's note: ship codes only for v1, the
full three-tier name-fitting cascade is a later refinement pass — do not
attempt the full cascade now).
```
**Verify:** codes are legible and correctly placed. Commit.

---

### Prompt 4 — Pan and zoom

```
Phase 4, step 4 only: add pan and zoom via react-simple-maps'
ZoomableGroup, per DESIGN.md §A.4/A.5 — this is the primary mechanism for
reaching small states, not a dropdown. Add the two quick-zoom shortcut
chips ("Northeast", "Delhi NCR") that smoothly pan/zoom the camera on
click. Do not add the islands inset yet.
```
**Verify:** zoom/pan works smoothly on desktop; quick-zoom chips work. Commit.

---

### Prompt 5 — Click-through to focused state view

```
Phase 4, step 5 only: wire state clicks to navigate to the existing
/tab1/state/:id route. Build out StateDetail.jsx per DESIGN.md §A.3: an
enlarged single-state map in the foreground, the national map dimmed
behind it, a stats panel fetching that state's full metric set from the
existing /api/v1/analytics endpoint (single state code), with the
currently-active metric from the selector shown first/emphasized. Add a
minimize control that navigates back to /tab1.
```
**Verify:** click a state, confirm the focused view and its data are correct, minimize returns cleanly, browser back/forward work. Commit.

---

### Prompt 6 — Islands inset

```
Phase 4, step 6 only: add the fixed inset box for Andaman & Nicobar and
Lakshadweep per DESIGN.md §A.5, as a second small MapView instance in a
corner of the national view — always visible, not tied to zoom level.
```
**Verify:** islands render correctly and are independently clickable into their own focused view. Commit.

---

## After Prompt 6

Phase 4 is done. Do a final full manual click-through against `DESIGN.md` Part A as a checklist before telling Codex to proceed to Phase 5 — this is exactly the kind of check that's cheap for you and expensive for Codex to self-verify.
