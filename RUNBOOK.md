# RUNBOOK.md

Operating notes for working efficiently with Codex on this project. Read this alongside `AGENTS.md`. Its purpose is narrow: stop Codex from re-discovering the same environment quirks via trial and error every session, since that's where a large share of tokens has gone so far, not actual feature work.

---

## 1. Known environment facts (don't rediscover these)

- **Python is invoked as `py`, not `python`**, on this machine.
- **Docker Desktop must be manually launched** before `docker compose up` will work, and takes roughly 1–2 minutes to become ready after launch. Poll rather than assume it's instant.
- **Tailwind's native Windows binary needs elevated/approved execution** under the sandbox (`spawn EPERM` otherwise) — for both `npm run build` and `npm run dev`. Expect to approve this every session unless the sandbox policy is changed.
- **`venv` creation can fail on `ensurepip`** due to a Windows temp-directory permission issue — this is environmental, not a code problem. Fix: delete the partial `.venv` and recreate with elevated permission approved up front, rather than retrying blind.
- **npm needs network access approved** for optional type packages (`@types/react`, etc.) not present in a restricted local cache — approve this once per fresh install, not per package.
- **pytest cache cleanup sometimes needs elevated deletion permission** for leftover temp folders from a previous run.

**When starting a new Codex session, front-load these as known facts** in the kickoff prompt (see §3) instead of letting Codex hit each one individually — this alone should cut several tool-call round trips per session.

---

## 2. Git — commit after every phase, starting now

The repo is not yet a git repository as of the end of Phase 3. **Fix this before Phase 4 starts:**

```
git init
git add .
git commit -m "Phases 0-3: backend scaffold, DB schema + seed, API endpoints, frontend routing"
```

Then commit at the end of every phase going forward. This matters for token efficiency specifically, not just safety:
- A future session can resume from `git log`/`git diff` against a known commit instead of you re-pasting a huge conversation transcript as context (which is itself expensive).
- If a phase goes sideways, `git reset`/`git revert` is a free rollback instead of Codex spending tokens debugging its way back to a working state.
- Codex can be told "diff against HEAD, don't restate what's already committed" — much cheaper than re-establishing context from scratch.

---

## 3. Session kickoff template (use this instead of pasting full history)

```
Resume this repository from its current git state (see `git log`). Do not
restate or redo anything already committed. Read AGENTS.md for
non-negotiables, RUNBOOK.md §1 for known environment facts (do not
re-discover these), and [ROADMAP.md phase / specific task] for what to
build next. Ask only if something is genuinely ambiguous after reading
those files.
```

This replaces re-attaching the full prior conversation, which is expensive and mostly unnecessary once git history exists.

---

## 4. Command-approval strategy

Per the earlier discussion on the destructive-command prompt: blanket "don't ask again" approval is fine for a narrow set of **safe, non-destructive** command prefixes, and should never be used for anything destructive.

**Safe to blanket-approve** (read-only or idempotent-build commands): `npm run build`, `npm run dev`, `pytest`, `alembic current`, `docker compose ps`, `python -m compileall`.

**Always approve individually, never blanket**: anything with `Remove-Item`, `git push`, `alembic upgrade`/`downgrade` (schema changes), reseeding the database, or anything touching `.env`/secrets.

---

## 5. Verification: let yourself do the cheap part

Codex has been spinning up and tearing down background `uvicorn`/`vite` processes and probing them via PowerShell for every verification step. For anything **visual** (Tab 1's map, Tab 2's layout), this is worse than useless — an HTTP 200 doesn't tell you a map renders correctly, and it costs real tool-call tokens to set up. From Phase 4 onward:

- Have Codex confirm the build/test/type-check passes (cheap, worth automating).
- **You** open `http://localhost:5173` yourself and eyeball the actual UI — this is free, and it's the only way to actually verify a visual feature anyway.
- Only ask Codex to run a live server + probe when you specifically need a JSON response verified (API correctness), not for anything you can just look at.

---

## 6. Scope prompts tightly, especially for Phase 4/5

Phase 4 (Tab 1) is the largest remaining phase. Don't ask for it in one prompt — a "build Tab 1" instruction produces a large diff that's expensive to generate, expensive to review, and expensive to fix if something's wrong. Break it into the sequence in `PHASE4_PROMPT_SEQUENCE.md` — one focused sub-task per prompt, verify, commit, move to the next. Same principle applies to Phase 5 (Tab 2) once you get there — happy to write that sequence when you're ready for it.

---

## 7. Consider a hybrid split for boilerplate

For component-level code that doesn't need the actual dev machine (e.g. a first-pass `MetricSelector.jsx`, `stateColors.js`, chart component skeletons), it can be cheaper to have this drafted outside Codex — I can write these directly against `DESIGN.md`/`ARCHITECTURE.md` — and hand them to Codex with a narrow "integrate this, wire it to the live API, don't rewrite the logic" instruction. That turns a "write feature from scratch" task (expensive) into an "integrate and verify" task (cheap), reserving Codex's tokens for the part that actually needs the local machine: running it, testing it against the real API, debugging real integration issues.
