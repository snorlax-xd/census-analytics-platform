# TAB1_AUDIT_FINDINGS.md

Findings from a screenshot-based review of the completed Phase 4 build
(Prompts 1–6, `PHASE4_PROMPT_SEQUENCE.md`), checked against `DESIGN.md`
Part A and `ARCHITECTURE.md`. This is the input to
`PHASE4_5_STABILIZATION_PROMPT_SEQUENCE.md` — read that file for the
actual fix plan; this file is the evidence and reasoning behind it.

Severity key:
- **BUG** — behavior contradicts the written spec, or is internally
  inconsistent (e.g. impossible data value). Not a matter of taste.
- **UX** — matches the spec's letter but fails its intent, or is the kind
  of rough edge the person building this flagged as "not dynamic enough."
- **DESIGN SYSTEM** — a missing shared primitive that both Tab 1 (now)
  and Tab 2 (next) will need; worth building once rather than twice.

---

## BUGS

### BUG-1 — StateDetail does not implement DESIGN.md §A.3 at all
**Evidence:** screenshot of `/tab1/state/UP`.

`DESIGN.md` §A.3 specifies: *"Enlarged single-state map in the
foreground; national map dimmed/blurred behind."* What actually renders
is two plain side-by-side cards — a small state outline (smaller than
the stats panel next to it) and a flat list of metric boxes on white.
There is no dimmed national map, no foreground/background relationship,
no sense of having "drilled in." This is the current implementation's
biggest deviation from the written design and should be treated as a
missing feature, not a styling gap.

### BUG-2 — Impossible negative value: "Households With TV: -4.13%"
**Evidence:** same StateDetail screenshot.

A household TV-ownership rate cannot be negative. Two candidate causes,
both worth checking before assuming which:
1. A different measure (e.g. a growth-rate or rank-delta field) is bound
   to this row's display slot — a frontend mapping bug.
2. The seed/aggregation pipeline computed this rate incorrectly for at
   least one state — a backend data bug (check against the raw CSV for
   Uttar Pradesh specifically, the same kind of manual spot-check
   `ROADMAP.md` Phase 1 already required for the literacy rate).

Do not "fix" this by just formatting the sign away — find which of the
two it actually is first.

### BUG-3 — Raw category slugs shown to the user
**Evidence:** StateDetail screenshot shows category labels like
`sanitation_drinking_water`, `demographics` verbatim under each metric.

These are internal identifiers, not display text. `DESIGN.md` §B.5
already defines the six correct display names for Tab 2's category
sidebar (Demographics, Economy, Literacy, Infrastructure, Sanitation,
Drinking Water) — Tab 1's stats panel should use the same mapping. This
is listed as a bug, not a UX nitpick, because showing internal codes to
end users is a correctness issue, not a taste issue.

### BUG-4 — Islands inset renders as unreadable dots
**Evidence:** national map screenshots at multiple zoom levels and
metrics.

`DESIGN.md` §A.5 requires the Andaman & Nicobar / Lakshadweep inset to
remain a usable, recognizable, clickable region "at every zoom level."
In practice it renders as one or two faint dots with illegible micro
labels — functionally present but not usable. This fails the spec's own
stated intent even though the component technically exists.

### BUG-5 — Islands inset overlaps and obscures a state label
**Evidence:** Delhi NCR quick-zoom screenshot — the islands inset box
sits directly on top of, and partially hides, the "UP" label.

A fixed-position UI element overlapping map content it wasn't meant to
touch is a layout/z-index bug, not a design choice — nothing in
`DESIGN.md` describes the inset as allowed to obscure other regions'
labels regardless of current viewport.

---

## UX GAPS (spec technically met, intent isn't)

### UX-1 — Northeast cluster label collision at default zoom
**Evidence:** default population/sex-ratio/literacy screenshots — SK,
AR, AS, ML, NL, TR, MZ, MN labels overlap each other.

`DESIGN.md` §A.6 ships ISO-codes-only for v1 deliberately (full
three-tier cascade deferred) — that part is correct and should **not**
be "fixed" by jumping ahead to the full cascade. But even code-only
labels need basic collision avoidance; right now they're stacked
illegibly on top of each other, which the spec's "font-size floor,
never force an illegible fit" principle (§A.6) already implies should
not happen.

### UX-2 — No visual affordance that states are clickable
Nothing in the current render hints that a state can be clicked before
the user tries it. `DESIGN.md` explicitly rules out a *hover preview
layer* (§A.2, §A.9) — but a lightweight hover affordance (cursor change,
subtle outline) that reveals no data is not a preview layer and doesn't
violate that rule. Worth adding for basic discoverability.

### UX-3 — StateDetail stats panel has no visual hierarchy beyond the one emphasized metric
Every metric row below the emphasized top one looks identical: same
size, same weight, same spacing, regardless of category. Given six
underlying categories already exist in the data model, grouping by
category (even simply, without Tab 2's full sidebar) would make this
screen scannable instead of a flat data dump.

### UX-4 — Legend swatches are visually cramped
Screenshots show 5–6 legend buckets packed into one dense row with small
gaps — technically meets §A.7's "5–6 discrete buckets" requirement, but
the value ranges are hard to read at a glance.

### UX-5 — Metric selector and quick-zoom chips look identical
Both are pill-shaped buttons in the same visual weight, positioned near
each other, with nothing distinguishing "this changes what's colored"
from "this moves the camera." Low risk of confusion once learned, but
adds friction on first use.

### UX-6 — Overall visual flatness
No elevation/shadow anywhere, thin uniform borders everywhere, one
typographic weight doing most of the work. This is the concrete,
fixable version of "the UI doesn't feel dynamic" — not a request to
redesign, a request to add a typography scale and some depth.

---

## DESIGN SYSTEM GAPS (shared primitives Tab 2 will also need)

### DS-1 — No shared category/measure display-name formatter
Needed by: Tab 1's stats panel (BUG-3) and Tab 2's category sidebar +
scorecard (`DESIGN.md` §B.5) identically. Build once, in `lib/`, use in
both places.

### DS-2 — No shared spacing/typography/elevation tokens
Currently every component seems to be styled ad hoc with inline Tailwind
utility choices rather than a small shared scale. `ARCHITECTURE.md` §6
already establishes the principle of shared modules for cross-tab
consistency (`stateColors.js`, `colorScale.js`) — the same principle
should extend to spacing/type/elevation so Tab 2 doesn't invent its own
variant of "what a card looks like."

### DS-3 — Confirm `lib/stateColors.js` is genuinely ready for reuse
Not used yet in Tab 1 by design (choropleth is metric-driven, not
per-state, per `ARCHITECTURE.md` §6) — this is correct and should stay
that way. Just confirm the module exists and is exported in the shape
Tab 2's bars/radar/badges will expect, before Tab 2 work starts, so it
isn't discovered missing mid-Phase-5.

---

## What this doc is NOT saying

- Not saying rebuild the map rendering — the boundary/winding work from
  the earlier debugging session is solid and shouldn't be touched.
- Not saying implement the full three-tier label cascade early — that's
  still correctly deferred per `DESIGN.md` §A.6.
- Not saying do Phase 6's full accessibility/mobile QA pass now — that
  stays in Phase 6 as planned.
- This is a scoped stabilization pass, not a redesign.
