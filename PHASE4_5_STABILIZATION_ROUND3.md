# PHASE4_5_STABILIZATION_ROUND3.md

Two previous attempts at BUG-4 (islands inset legibility) both reported
success and both are contradicted by a zoomed screenshot taken right
after the second attempt — Lakshadweep still renders as scattered dots,
Andaman & Nicobar as a barely-visible smudge. This is the actual root
cause and the fix, addressed properly this time.

**Send this as one prompt, verify with a zoomed screenshot before
declaring it done** — don't repeat the pattern of trusting a "fixed"
report without checking. Two rounds of that already happened here.

---

## Why the last two attempts didn't work

Andaman & Nicobar sits in the Bay of Bengal; Lakshadweep sits in the
Arabian Sea. They are roughly 3,000 km apart — further apart than
London and Moscow. The last fix computed a single `geoMercator().fitSize()`
bounding box across *both* regions' combined extent. A box that has to
span 3,000 km of open ocean to contain both archipelagos will always
render each individual island cluster as a tiny fraction of that box,
regardless of how large the inset panel itself is made. This is a
bounding-box geometry problem, not a file-size or scale-slider problem
— enlarging the inset panel (as the second attempt did, 190px → 300px)
could not have fixed it, and didn't.

## The actual fix: two independently-projected regions, not one shared box

```
Stabilization round 3, islands inset only: BUG-4 is still unresolved.
Root cause: the current implementation computes one shared
geoMercator().fitSize() bounding box across both Andaman & Nicobar AND
Lakshadweep combined. These two regions are ~3,000km apart (Bay of
Bengal vs. Arabian Sea), so any shared bounding box is dominated by
ocean between them, making each region render as a tiny fraction of the
box regardless of the inset panel's pixel size — confirmed by a zoomed
screenshot after the previous fix attempt, still showing Lakshadweep as
scattered dots and Andaman & Nicobar as a barely-visible smudge.

Fix: give each region its own independent projection, each fitted
tightly to only that region's own bounding box, not a shared one.
Render them as two separate small maps stacked or side-by-side within
the single ISLANDS inset panel (the panel itself stays one fixed corner
UI element per DESIGN.md §A.5 — this is about what's rendered inside it,
not adding a second inset panel). Each of the two mini-maps gets its own
geoMercator().fitSize() call scoped only to that single region's
feature(s), so Lakshadweep's cluster of small islands fills its own
mini-map at a legible scale, independent of how far away Andaman &
Nicobar is on the globe.

Also fix the bundle-size issue Codex flagged in its own last response:
do not import the full 26MB Frontend/src/assets/india-full-detail.json
just to filter out two features at runtime. Instead, add a one-time
preprocessing step (a small Node or Python script, following the same
pattern as Backend/scripts/prepare_boundaries.py's one-off-script
convention) that extracts only the Andaman & Nicobar and Lakshadweep
features from the full-detail source into a new, small standalone file
— e.g. Frontend/src/assets/india-islands-detail.json — committed
alongside the other boundary assets. The islands inset imports this
small file directly, not the 26MB national one. Report the new file's
size so we can confirm this actually shrunk the relevant import.

Do not touch the national map or StateDetail's map rendering — this is
scoped to the islands inset component only.
```

**Verify:** zoom into a screenshot of just the ISLANDS panel and confirm
Andaman & Nicobar's actual elongated archipelago shape and Lakshadweep's
cluster of distinct small islands are both clearly visible as shapes —
not dots, not a gray smudge. Confirm both are still independently
clickable into their own focused view. Confirm the new islands-only
asset file is meaningfully smaller than 26MB (should be a few KB to
low hundreds of KB, not megabytes). Commit only after the screenshot
actually shows recognizable shapes — not after reading Codex's summary
of what it did.

---

## Also re-check before closing Phase 4.5 (no new prompt needed unless something's wrong)

The inset was widened from 190px to 300px in the last round, *after*
BUG-5 (the inset overlapping the "UP" label during Delhi NCR zoom) was
already fixed. A wider inset is a plausible way to accidentally
reintroduce that overlap. Zoom into Delhi NCR one more time and confirm
the islands panel still doesn't cover any label. If it does, that's a
one-line CSS positioning fix, not a new investigation — no separate
prompt needed, just flag it in the same message as Round 3's prompt
above if you spot it before sending.

---

## After this is verified

Phase 4.5 is genuinely done. Update `PROJECT_STATUS.md`'s Phase 4.5 row
for BUG-4 to reflect the real fix and file size, then proceed to
`PHASE5_TAB2_PROMPT_SEQUENCE.md` starting with its conditional Prompt 0.
