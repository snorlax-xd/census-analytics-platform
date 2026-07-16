# PHASE4_5_STABILIZATION_ADDENDUM.md

Continuation of `PHASE4_5_STABILIZATION_PROMPT_SEQUENCE.md`. Prompts 1–6
from that file are confirmed done (verified against screenshots: BUG-2's
value is now positive and matches the CSV, formatMeasure.ts is applying
correctly, BUG-5's overlap is gone). Prompt 7 was interrupted mid-way by
a Codex usage limit and is only partially applied. Two issues that were
*claimed* fixed in the same response are confirmed, from direct
screenshots, to still be broken. This addendum is three prompts to
close all of that out before Phase 5 (Tab 2) starts.

**Send these one at a time, exactly as before. Do not merge them into
one message this time** — the last stabilization step showed that Codex
will happily execute a merged 3-prompt message and it came back clean,
but that was luck, not a reason to keep doing it. Bigger diffs are
harder to bisect if something's wrong, and Tab 2's diffs will be larger
than Tab 1's were.

---

### Prompt 8 — Finish the interrupted token-and-consistency pass

```
Continuing an interrupted step, not starting a new one: the previous
session added shared design tokens to Frontend/src/styles.css via
Tailwind v4's @theme, and made one edit to MapView.jsx adding a hover
class, before hitting a usage limit. Read both files as they currently
stand before changing anything — do not redo the token definitions,
only complete what's still missing from the original request:
1. Confirm the hover affordance on clickable state paths in MapView.jsx
   is fully wired (cursor change + outline only, no data preview, per
   DESIGN.md §A.2/§A.9) — finish it if it's only partially applied.
2. Apply the established tokens to the choropleth legend so its buckets
   have clearer spacing (UX-4) — currently still cramped per the latest
   screenshot.
3. Apply the established tokens to visually distinguish the metric
   selector button group from the quick-zoom shortcut chips (UX-5) —
   currently they look identical. Do not change either one's function.
4. Group StateDetail's metric rows by category, using formatMeasure.ts,
   with visible separation between category groups (UX-3) — currently
   still a flat undifferentiated list per the latest screenshot.
Do not touch anything else. Do not redesign colors or layout structure.
```
**Verify:** screenshot `/tab1` and confirm the legend is easier to scan,
the metric selector and zoom chips are visually distinct from each
other, and confirm a state's focused view now groups metrics under
visible category headers rather than one continuous list. Commit.

---

### Prompt 9 — Actually implement the dimmed national map behind StateDetail

```
BUG-1 is only half-fixed. The current StateDetail.tsx renders a correct
enlarged foreground map and stats panel, but DESIGN.md §A.3's
requirement that "the national map remains visible, dimmed/blurred, in
the background" was not implemented — there is currently no second map
rendered at all behind the focused view, just plain page background.
Fix this specifically: render MapView in its existing national
choropleth mode as a full-bleed background layer behind the focused
state's foreground panel, at reduced opacity and/or a CSS blur filter,
non-interactive (pointer-events disabled on the background layer so it
can't be accidentally clicked or zoomed while a state is focused). Do
not refetch data for this background layer if the same data is already
available from Tab 1's query cache for the currently active metric —
reuse it. Do not change the foreground composition, which is already
correct.
```
**Verify:** screenshot `/tab1/state/UP` again and confirm you can now
actually see the dimmed/blurred outline of the rest of India behind the
enlarged Uttar Pradesh panel — not just empty background. Commit.

---

### Prompt 10 — Properly fix islands legibility (BUG-4, real fix this time)

```
BUG-4 is still unresolved despite a previous attempt — a zoomed
screenshot of the ISLANDS inset shows Andaman & Nicobar and Lakshadweep
still rendering as small dark specks with no recognizable landmass
shape, not the "clear, recognizable shapes" DESIGN.md §A.5 requires.
Diagnose before patching: check whether the inset's MapView instance is
currently reusing the same simplified national-view geometry (which,
being simplified across all 35 regions at once, may have stripped these
two small archipelagos down past the point of visibility) instead of
loading Frontend/src/assets/india-full-detail.json filtered to just
these two features. If so, switch the inset specifically to the
full-detail source, filtered to AN and LD only, with its own
independent geoMercator().fitSize() call scoped tightly to just those
two features' combined bounding box (not the national map's projection)
so they fill the inset box at a legible scale. Increase the inset box's
pixel dimensions if the current size is part of the problem. This is
about this one component's rendering only — do not touch the national
map's or StateDetail's map rendering.
```
**Verify:** zoom into the ISLANDS inset screenshot again and confirm
Andaman & Nicobar's actual archipelago shape and Lakshadweep's cluster
of small islands are now visually distinguishable, not dots. Confirm
they're still independently clickable into their own focused view
(don't regress that from the earlier Phase 4 Prompt 6 work). Commit.

---

## After Prompt 10

Do the full manual click-through against `DESIGN.md` Part A one more
time — this is the second and final check for Tab 1 before Phase 5
starts. Only once this is clean should Tab 2 work begin; Tab 2's mini
map reuses `MapView` directly; an unresolved rendering bug here would
otherwise carry straight into Tab 2.
