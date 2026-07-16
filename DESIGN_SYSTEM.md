# DESIGN_SYSTEM.md

Reference for the shared visual language established during Phase 4.5
stabilization. Tab 2 will introduce many new component types (scorecard,
diverging bar chart, radar chart, verdict card, badges) that have no
Tab 1 equivalent — this doc exists so those get built against the same
tokens instead of each inventing its own spacing/color/shadow choices,
which is exactly the inconsistency Phase 4.5 was created to prevent from
happening twice (see `ARCHITECTURE.md` §6's shared-module principle,
extended here from map/color to general UI tokens).

**This file's token names are placeholders pending the actual token
names Prompt 8 lands on in `Frontend/src/styles.css`'s `@theme` block.**
Before starting Phase 5, replace every `<...>` below with the real
token names from that file, so this becomes copy-pasteable ground truth
for Codex rather than a guess. This file is intentionally structured so
that step is a quick fill-in, not a rewrite.

---

## 1. Where tokens live

Tailwind v4, CSS-first config. Tokens are defined in
`Frontend/src/styles.css` inside an `@theme` block, not in a JS
`tailwind.config.js`. Any new component uses the resulting utility
classes (e.g. `bg-<token-name>`, `p-<token-name>`) — it does not
hardcode raw hex colors, arbitrary pixel spacing (`p-[13px]`), or
one-off shadow values.

## 2. Spacing scale

`<list the confirmed spacing scale values here, e.g. xs/sm/md/lg/xl and
their pixel equivalents, once Prompt 8's diff is reviewed>`

Rule going forward: every new Tab 2 component (scorecard rows, chart
containers, category sidebar items) picks its padding/gaps from this
scale. No new spacing values get introduced without a reason recorded
here.

## 3. Typography scale

`<list the confirmed type sizes/weights here>`

Established need (from `TAB1_AUDIT_FINDINGS.md` UX-6): at least 3
distinct weight/size combinations beyond the browser default, used
consistently for: page/section titles, metric values (the large
numbers), and metadata/category labels (the small gray text under each
metric). Tab 2's scorecard numbers and the verdict card's headline
sentence should map onto these same three tiers rather than introducing
a fourth.

## 4. Elevation / shadow scale

`<list the confirmed shadow values here>`

Used for: StateDetail's foreground panel (Phase 4.5 Prompt 9), and
should extend to Tab 2's scorecard card, each chart's container, and the
verdict card — anything that reads as "a panel sitting above the page,"
consistent with how Tab 1's focused view now establishes that pattern.

## 5. Color usage — two independent systems, do not merge

Per `ARCHITECTURE.md` §6, restated here because Tab 2 is where mixing
them becomes an easy mistake to make:

- **`lib/colorScale.js`** — metric-value-driven, quantile-based. Used
  only by Tab 1's choropleth. Tab 2 does not use this for anything.
- **`lib/stateColors.js`** — one fixed color per state/UT, identity-based
  not value-based. Used by Tab 2's bars, radar lines, badges, mini-map
  highlight outlines, and Tab 1's selection/highlight color (not its
  choropleth fill).

Before Phase 5 starts, confirm `lib/stateColors.js` actually exports a
usable `getStateColor(isoCode)`-shaped function with all 35 codes
covered (DS-3 from `TAB1_AUDIT_FINDINGS.md`) — if it's still a stub,
that's a Phase 5 Prompt 1 prerequisite, not something to discover
mid-chart-building.

## 6. Category display names — single source of truth

`Frontend/src/lib/formatMeasure.ts` (built in Phase 4.5 Prompt 3) is the
only place category-slug-to-display-name and measure-name formatting
happens. Tab 2's category sidebar (`DESIGN.md` §B.5) and scorecard rows
import from this file. Do not re-derive display names locally in any
Tab 2 component.

## 7. Motion

Established in `DESIGN.md` §B.6.3 directly (not a Phase 4.5 addition,
restated here for completeness since it's a token-like decision): all
Recharts instances use `isAnimationActive` (default, do not disable) and
an explicit `animationDuration` of ~500ms with an ease-out curve,
applied consistently across every chart type so multiple charts updating
together (e.g. after a state swap) feel synchronized rather than
staggered arbitrarily.

## 8. Hover affordance convention

Established in Phase 4.5 Prompt 8/9: clickable map regions get a cursor
change plus a subtle outline on hover — never a data preview, tooltip,
or value display of any kind, per `DESIGN.md` §A.2/§A.9's explicit ban
on a hover preview layer. This convention extends to Tab 2's mini map
and any future clickable map surface.

---

## Maintenance note

When Phase 5 introduces a genuinely new visual primitive that doesn't
fit an existing token (e.g. the verdict card's ▲/▼ delta indicator
color), add it here with the same "why" reasoning style as the rest of
this file, rather than letting it live undocumented only in the
component that first used it.
