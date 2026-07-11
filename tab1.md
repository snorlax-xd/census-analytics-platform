# Tab 1: National Map Explorer — Specification

Census Analytics Platform — Tab 1 covers the national map view and the focused single-state view. This document captures the complete decided structure, including the reasoning behind each decision.

---

## 1. Overview

Tab 1 is a single continuous, interactive map of India (all states and Union Territories) that:
- Shows a chosen key metric as a choropleth (color-coded) layer, with the metric's value labeled directly on each state.
- Lets the user click any state to open a focused, detailed view of that state in the foreground, with the national map dimmed in the background.
- Lets the user minimize back to the national view at any time.

No hover-based preview layer. No dropdown-based state picker. Interaction is deliberately kept to two mechanisms: **metric selection** and **click**.

---

## 2. Interaction model

### 2.1 Metric selector
- A control above the map (button group or select, not a dropdown reused from elsewhere) lets the user choose which metric colors the map: population, population density, sex ratio, literacy rate (list extensible later).
- Changing the metric:
  - Recolors every state's fill according to that metric's value.
  - Updates the numeric label shown on each state to that metric's value (not always population).
  - Updates the legend to reflect that metric's buckets and range.
- This is the **only** mechanism for previewing data at the national level — there is no separate hover tooltip and no separate "quick preview" state. What you see on the map *is* the current metric's value, per state, at all times.

### 2.2 Click → focused state view
- Works identically on desktop and mobile — no hover dependency anywhere in the interaction.
- Clicking/tapping a state transitions to a **focused state view**:
  - Real, addressable route, e.g. `/tab1/state/maharashtra` — not just a client-side modal toggle. This means browser back/forward, refresh, and direct links all work correctly.
  - Enlarged map of that single state rendered in the foreground.
  - The national map remains visible, dimmed/blurred, in the background.
  - A stats panel shows the state's full set of key metrics.
    - The metric currently active in the metric selector is emphasized/shown first in the panel (continuity: whatever the user was just scanning for stays visually primed when they drill in).
    - All other tracked metrics follow below it.
- A **minimize control** in the focused view returns to the national view (equivalent to navigating back to the root route).

### 2.3 What was deliberately removed
- No hover-triggered tooltip/preview layer — decided against once the metric selector already surfaces the relevant value directly on the map.
- No dropdown/searchable-combobox as a workaround for hard-to-click tiny states — see §4, replaced by pan/zoom instead.

---

## 3. Map rendering

### 3.1 Data source
- Boundary and metric data sourced exclusively from **official Indian government sources** (Census of India GIS data / Survey of India boundary data).
- A single authoritative boundary source is used throughout — national view and focused state view both derive from the same source, to avoid pixel-level mismatches at internal state borders that come from mixing an official source with third-party GeoJSON packages.

### 3.2 Two levels of boundary detail
- **National (zoomed-out) view**: uses a *simplified* version of each state's boundary polygon — far fewer coordinate points than the raw official data, since fine coastline detail isn't visible at that zoom level anyway.
- **Focused state view**: loads the *full-detail* boundary for that one state only.
- Simplification is a **one-time preprocessing step** (e.g. via `mapshaper`), not something computed at request time or in the browser.
- Reasoning: loading full-detail polygons (thousands of points for coastline-heavy states like Gujarat or Odisha) for all 36 states/UTs simultaneously at national zoom would slow initial load and cause laggy pan/zoom, especially on lower-end phones, for detail the user can't even perceive at that zoom level.

### 3.3 Pan and zoom
- The national map supports standard interactive pan and zoom: scroll-to-zoom + drag-to-pan on desktop, pinch-to-zoom + drag-to-pan on touch devices.
- This is the **primary mechanism for handling small and visually clustered states/UTs** (see §4) — replacing static inset panels or leader-line callouts as the default solution. Nothing extra renders on screen until the user actually zooms in on a region.

---

## 4. Handling small/clustered states and UTs

### 4.1 Why this needed a decision
At national zoom, several states/UTs are too small to click accurately or to fit a readable label: the North-East cluster (Sikkim, Assam, Meghalaya, Tripura, Mizoram, Manipur, Nagaland, Arunachal Pradesh), and isolated small ones (Goa, Delhi, Chandigarh, Puducherry, Dadra & Nagar Haveli and Daman & Diu).

### 4.2 Decided approach: pan/zoom over permanent insets
- Rejected: permanently rendering separate inset boxes for clusters plus leader lines for isolated small states all at once — this was judged too visually busy, especially on mobile, and borrows an unnecessary constraint from print cartography (which can't zoom, so it has to use insets; a live interactive map doesn't have that constraint).
- Adopted instead:
  - Users zoom into any region naturally via pan/zoom (§3.3). As a state grows on screen, its click target and label both become viable without any extra UI.
  - **Quick-zoom shortcut chips** above the map (e.g. "Northeast", "Delhi NCR") smoothly pan-and-zoom the camera to that region on tap. These are navigation shortcuts, not a data-selection dropdown, and are optional — zoom/pan works without them too.

### 4.3 One exception: fixed inset for offshore islands
- **Andaman & Nicobar Islands and Lakshadweep** remain a fixed small inset box in a corner of the map, always visible, at every zoom level.
- Reasoning: these territories are genuinely distant from the mainland — no reasonable amount of zoom solves this without wasting most of the canvas on empty ocean. This is standard convention on essentially every map of India, digital or print, and is treated as a fixed requirement rather than a fallback.

---

## 5. State labeling logic

A three-tier cascade, evaluated **at render time** against the actual rendered bounding box of each state's polygon at the current zoom/viewport — not precomputed or hardcoded per state, since the same state may fit its full name on a wide desktop view but only its code on a narrow mobile view.

1. **Full state name** (e.g. "Maharashtra") — used if it fits within the rendered polygon at a legible size.
2. **Standard ISO 3166-2:IN code** (e.g. "MH", "GJ", "TN") — used if the full name doesn't fit. Using the standardized code (rather than inventing abbreviations) guarantees uniqueness across all states/UTs.
3. **Leader-line callout** — used if even the code doesn't fit legibly. A short line points from the state's centroid out to a label placed in nearby whitespace.

Implementation details:
- **Font-size floor**: text is never shrunk below a minimum legible size (~9–10px) to force a fit — if it would need to go smaller than that, treat it as "doesn't fit" and fall to the next tier.
- **Leader-line collision avoidance**: leader-line endpoints are routed to a small set of fixed "safe margin" slots around the map edge, assigned by nearest-available-slot rather than left to collide with each other. In practice, with pan/zoom now handling most of the small-state problem (§4), leader lines are a rare fallback rather than a common default — mainly relevant within the fixed islands inset itself if needed.

---

## 6. Choropleth coloring

- Coloring uses a **quantile or natural-breaks (Jenks) scale**, not a naive linear scale — population and most census metrics are heavily right-skewed (e.g. Uttar Pradesh and Bihar vs. the rest), and a linear scale would make most of the map look flat.
- The legend shows 5–6 discrete color buckets with their value ranges, and **updates whenever the metric selector changes**.

---

## 7. Data vintage

- All data for this phase is sourced from **Census 2011** only. Multi-year census comparison is explicitly deferred to a later phase.
- A persistent, small "Data as of Census 2011" label is shown on the map view at all times (e.g. bottom corner) — kept even at single-year scope, so there's no retrofit needed later when more years are added.
- The underlying versioned measure vocabulary (already part of the platform's schema design) anticipates this expansion, so no schema rework will be needed to add later census years.

---

## 8. Performance summary

- Two boundary resolutions (simplified for national view, full-detail for focused view), precomputed via offline simplification tooling — not computed live.
- Pan/zoom interactions operate on the simplified geometry at national zoom; full detail loads only on transition into a focused state view.

---

## 9. Explicitly out of scope (for now)

- **Accessibility** (colorblind-safe palette, keyboard navigation, screen-reader support) — deliberately not a focus for this phase. Flagged as a backlog item, not a blocked or abandoned requirement.
- **Multi-year census analysis** — deferred; current scope is Census 2011 only.
- **Hover-based preview layer** — removed entirely in favor of the metric-selector + click model (§2).
- **Dropdown/search as a click-target fix** — replaced by pan/zoom + quick-zoom shortcuts (§4).

---

## 10. Open items for next pass

- Finalize the exact v1 metric list beyond population (density, sex ratio, literacy rate confirmed — anything else?).
- Confirm which quick-zoom shortcut chips to ship in v1 (Northeast and Delhi NCR proposed; islands don't need one since they're a fixed inset already).
- Decide the specific color ramp per metric (e.g. one ramp for population-type metrics, a diverging ramp for something like sex ratio where "average" has a meaningful center point).
