# PROJECT_STATUS.md

Single accurate status snapshot, written to correct for the gap between
what a Codex response *claims* was done and what screenshots actually
confirm. Update this file at the end of each phase rather than trusting
a chat summary alone — this session found two cases (BUG-1's background
dimming, BUG-4's islands) where the claimed fix and the actual rendered
result didn't match, and only a direct screenshot caught it.

---

## Phase 0 — Environment: DONE, verified
## Phase 1 — Database & real data: DONE, verified (Maharashtra literacy spot-check matched CSV exactly)
## Phase 2 — Backend API: DONE, verified (all three endpoints tested including edge cases — island neighbor returns null, not an error)
## Phase 3 — Frontend scaffolding: DONE, verified
## Phase 4 — Tab 1 core build (Prompts 1–6): DONE, verified, including the boundary-rendering bug (ring winding) fully diagnosed and fixed — see `SESSION_HANDOFF.md` for that debugging history in full.

## Phase 4.5 — Tab 1 Stabilization: IN PROGRESS

| Item | Status | Evidence |
|---|---|---|
| BUG-2 (impossible negative TV% value) | **Fixed, verified** | Live API confirmed `television_households_pct = 24.2079`, matches CSV |
| DS-1 (formatMeasure.ts) | **Fixed, verified** | Screenshot shows "Demographics"/"Economy" category labels, no raw slugs |
| BUG-1 (StateDetail layout) | **Partially fixed** | Foreground (enlarged map, stats panel, minimize, emphasis) confirmed correct via screenshot. Dimmed background national map — confirmed **missing entirely**, not just subtle, via screenshot. Needs `PHASE4_5_STABILIZATION_ADDENDUM.md` Prompt 9. |
| BUG-5 (islands inset overlapping UP label) | **Fixed, verified** | Islands moved to a separate side rail, no overlap in screenshot |
| BUG-4 (islands rendering as illegible dots) | **Not fixed, despite an earlier claim it was** | Zoomed screenshot confirms AN/LD are still unrecognizable specks. Needs `PHASE4_5_STABILIZATION_ADDENDUM.md` Prompt 10, with a real root-cause diagnosis this time (likely: inset reusing simplified national geometry instead of full-detail, filtered) |
| UX-1 (NE label collision) | **Likely fine as-is** | At default national zoom, NE cluster is still visually tight, but per `DESIGN.md` §A.5 this is expected — pan/zoom and the "Northeast" quick-zoom chip are the intended solution, not fitting everything at national zoom. Not re-flagging as broken. |
| Prompt 7 (design tokens) | **Interrupted by a Codex usage limit, partially applied** | Only the token definitions in `styles.css` and one line of `MapView.jsx` landed. Legend spacing, selector/chip differentiation, and StateDetail category grouping did not. Needs `PHASE4_5_STABILIZATION_ADDENDUM.md` Prompt 8. |

**Remaining before Phase 4.5 is closeable:** Addendum Prompts 8, 9, 10,
sent one at a time, each verified with a fresh screenshot before moving
to the next — not batched, unlike the previous 4–6 merge.

## Phase 5 — Tab 2: NOT STARTED
Plan: `PHASE5_TAB2_PROMPT_SEQUENCE.md`, 11 prompts (+ a conditional
Prompt 0 to confirm `stateColors.js` is genuinely ready). Backend
confirmed already sufficient — no backend work expected in this phase.

## Phase 6 — Polish: NOT STARTED
## Phase 7 — RBAC: NOT STARTED (correctly not begun — depends on Phase 6)
## Phase 8 — Deployment: NOT STARTED

---

## Process notes worth carrying forward

1. **A Codex response claiming something is fixed is not the same as it
   being fixed.** Two of three claims in the last stabilization batch
   didn't match their own screenshots. Always screenshot-check after a
   visual change before marking a bug closed, especially ones that were
   already gotten wrong once.
2. **Send one prompt at a time.** It got away with a 3-prompt merge once
   in Phase 4.5 — don't treat that as proof it's safe, especially for
   Tab 2's larger diffs.
3. **Watch for Codex usage-limit interruptions mid-step**, as happened
   on Prompt 7. When resuming, tell Codex explicitly what's already
   landed so it doesn't redo completed work or, worse, conflict with it.
4. **The boundary-rendering bug earlier in this project (ring winding
   through mapshaper) is the template for how to debug something like
   this**: get a numeric signal instead of trusting a screenshot, isolate
   one variable in a throwaway test, verify a fix actually landed on disk
   before re-testing, and suspect a pipeline stage between the fix and
   the observation if a provably-correct fix still doesn't show up.
   `SESSION_HANDOFF.md` has the full walkthrough if this class of bug
   resurfaces.
