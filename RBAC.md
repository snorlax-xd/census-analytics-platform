# RBAC.md

Role-based access control design for the Census Analytics Platform.

**Status: not implemented yet — deferred to Phase 7.** See `AGENTS.md` and `ROADMAP.md` for why: RBAC only gates the data-curation side of the platform, and that flow doesn't exist yet. Building auth/JWT scaffolding before there's a protected endpoint to test it against is pure overhead. This document exists so the design is settled on paper before that phase starts, not so it gets built early.

---

## 1. Framing

Census data itself is public-domain information. RBAC here is **not** about hiding data from viewers — both Tab 1 and Tab 2 remain public, unauthenticated, read-only, always. RBAC controls only who can **modify, curate, and publish** data.

---

## 2. Roles

| Role | Can do |
|---|---|
| **Guest** | Full read access to Tab 1 and Tab 2. No login. Default for essentially everyone. |
| **Registered user** | Everything a Guest can, plus saved comparisons, bookmarked states, personal dashboards. Adds no data-modification permissions. |
| **Data curator** | Upload new reference data, edit measure definitions, create new data versions in draft. Cannot manage users. |
| **Admin** | Everything a curator can, plus manage user accounts/role assignments, and **publish** a data version to production (a distinct, deliberate action from editing a draft). |

---

## 3. Implementation approach (when this phase starts)

- **Auth:** `OAuth2PasswordBearer` in FastAPI, JWT issued on login carrying `user_id` and `role` as claims.
- **Route protection:** a single reusable dependency, e.g. `require_role(["curator", "admin"])`, attached only to routes that need it. Tab 1/Tab 2's existing read endpoints (`/api/v1/analytics`, `/api/v1/presets/*`) get **no** dependency added — they stay open.
- **Schema:**
  - `users` — `id, email, hashed_password, created_at`
  - `roles` — `id, name`
  - `role_permissions` — many-to-many, so finer-grained permissions (e.g. "can edit draft" vs. "can publish") can be added later without a code change, only a data change.
  - `audit_log` — `user_id, action, target, timestamp, old_value, new_value` — every edit/publish action recorded. Non-negotiable once curation exists; this is what answers "who changed this number and why."
- **Publish vs. edit distinction:** curators can freely edit a *draft* version of a measure/dataset. Making that draft the live version everyone sees is a separate, admin-only action. This protects the live Tab 1/Tab 2 views from an in-progress edit going out half-done, and ties into the versioned measure vocabulary already anticipated in `DATABASE.md`.
- **Frontend:** decode the JWT role claim client-side only to conditionally show/hide edit UI — never treat hiding a button as real authorization. Every protected action must be re-checked server-side regardless of what the frontend shows.

---

## 4. What NOT to do

- Do not add JWT middleware to `/api/v1/analytics` or `/api/v1/presets/*` — these must remain public.
- Do not build the `users`/`roles` tables or any login UI before there's an actual curator workflow (data upload, measure editing) for them to protect.
- Do not skip the audit log once this phase starts — it's cheap to add up front and expensive to retrofit.
