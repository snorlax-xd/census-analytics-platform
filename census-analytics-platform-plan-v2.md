# Census Analytics Platform — Development Plan (v2)

**Scope:** Census-related datasets only (Census 2011 as seed, extensible to 2001, SECC, future editions)
**Stack:** React (frontend) · Python (backend) · PostgreSQL (database)
**Phase:** V1 foundation. AI/RAG/NL-querying explicitly deferred to Phase 2.
**Reference datasets used to validate this plan:** `india-districts-census-2011.csv` (district-level demographics), `india_census_housing-hlpca-full.csv` (district-level housing, rural/urban split)

---

## 1. Guiding Principles

1. **One domain, understood deeply** — not a generic data platform. Every decision assumes the data is Census-shaped: geography-indexed, demographic, tabular, batch-updated.
2. **Grain and geography are the spine.** Every table, chart, and query reduces to "which measure, at which geography level, for which locale/year/dataset."
3. **Human confirms, system suggests.** No AI in V1 — matching relies on deterministic rules + human confirmation.
4. **Simple before clever.** One flexible fact table beats a table per dataset. Refetch-on-change beats websockets until proven insufficient.
5. **Never silently guess or silently drop.** Unmatched columns, unmatched geographies, and missing rows must be surfaced, not assumed away.

---

## 2. What the Reference Datasets Actually Confirmed

Before designing further, here's what the two real files tell us — this replaces guesswork with fact.

| Finding | Detail | Design implication |
|---|---|---|
| Both files are district-grain | 640 districts, 35 states, in both files | Confirms district-level as the right V1 grain |
| District code is a reliable join key | Codes 1–640 identical across both files | Use `district_code` as the canonical geography ID — no fuzzy matching needed between these two sources |
| State name spelling differs | `"JAMMU & KASHMIR"` vs `"JAMMU AND KASHMIR"` across the two files | Real, small-scale proof that a name-normalization step is still needed even with clean data |
| Housing file has an extra dimension | 3 rows per district: Rural / Urban / Total | Geography + measure isn't enough — need a **locale** dimension |
| Housing file values are percentages, not counts | e.g. "Total Number of households" = 100 in every row (a normalized base) | Need a `value_type` flag (`count` vs `percentage`) on every measure — never aggregate the two the same way |
| 12 districts missing a locale row | e.g. fully urban districts have no "Rural" row | Import must tolerate legitimately missing combinations, not reject them |
| File 1 has zero nulls, one row per district | Clean, wide, raw counts | This is the easy case — good first dataset to load |

---

## 3. Domain Modeling (paper stage — revised)

### 3.1 Geography hierarchy
```
Country
 └── State
      └── District
```
V1 scope: **district level only** (confirmed by both reference files). Subdistrict/village deferred — the housing file's tehsil/ward/village columns are present but always zero at this grain, so they're not needed yet.

### 3.2 Core dimensions (not just measures — this is the one real addition worth keeping from the review)
Every data point in this platform is described by four things, not three:
- **Geography** — which district (state → district)
- **Measure** — what's being measured (population, literacy_rate, etc.)
- **Locale** — rural / urban / total (defaults to `total` if a dataset doesn't split it)
- **Dataset/year** — which upload and edition this value came from

This four-part shape is simple enough to keep in one table (Section 4.4) — it's not the heavier "Dimension/Attribute/Measure/Observation" model from the refinement pass, which would be over-engineering for a single, well-understood domain.

### 3.3 Core measures (fixed, versioned vocabulary)
Two categories, tagged explicitly by `value_type`:
- **Count-based** (from files like the district census): `total_population`, `male_population`, `female_population`, `literate`, `sc_population`, `st_population`, `total_workers`, etc.
- **Percentage-based** (from files like the housing dataset): `pct_good_condition_housing`, `pct_lpg_cooking`, `pct_electricity_access`, `pct_own_latrine`, etc.

Never sum or average across `value_type`s without explicit, visible conversion logic. This distinction didn't exist in v1 of this plan — it's the most important correction from analyzing real data.

### 3.4 Locale
Fixed enum: `rural`, `urban`, `total`. Any dataset without a locale breakdown gets every row tagged `total` by default — no schema branching needed for datasets like the district census file.

---

## 4. Database Schema (PostgreSQL)

### 4.1 Design philosophy
Same hybrid approach as before: normal relational tables for structure/reference, one tall fact table for actual values. Two changes from v1: add `locale`, add `value_type`.

### 4.2 Core tables

**`geography`**
| column | type | notes |
|---|---|---|
| id | serial PK | |
| district_code | int, unique | matches Census official district code (1–640 confirmed) |
| district_name | text | |
| state_name | text | |
| state_name_normalized | text | lowercase, punctuation-stripped, for matching across sources |

**`dataset`**
| column | type | notes |
|---|---|---|
| id | serial PK | |
| name | text | |
| year | int | |
| source | text | e.g. "Census of India 2011 — District Profile" |
| status | enum (`processing`,`pending_confirmation`,`active`,`archived`) | |
| uploaded_at | timestamp | |
| version | int | |

**`measure`**
| column | type | notes |
|---|---|---|
| id | serial PK | |
| key | text, unique | e.g. `literacy_rate`, `pct_lpg_cooking` |
| display_name | text | |
| value_type | enum (`count`,`percentage`) | **new** — prevents mixing counts and percentages |
| unit | text | e.g. "%", "persons" | |

**`fact_data`** (core tall table)
| column | type | notes |
|---|---|---|
| id | bigserial PK | |
| dataset_id | FK → dataset.id | |
| geography_id | FK → geography.id | |
| measure_id | FK → measure.id | |
| locale | enum (`rural`,`urban`,`total`) | **new**, defaults to `total` |
| value | numeric | |

Composite index: `(dataset_id, geography_id, measure_id, locale)` — the query hot path.

**`column_mapping`** (upload audit trail)
| column | type | notes |
|---|---|---|
| id | serial PK | |
| dataset_id | FK → dataset.id | |
| source_column_name | text | raw header, e.g. `"Households_with_Internet"` |
| mapped_measure_id | FK → measure.id, nullable | |
| confirmed_by_user | boolean | |

**`users`** (minimal)
| column | type | notes |
|---|---|---|
| id | serial PK | |
| email | text | |
| role | enum (`admin`,`analyst`,`viewer`) | |

### 4.3 Why this shape handles what we found in the real data
- Housing file's Rural/Urban/Total → `locale` column, no schema branching.
- Housing file's percentage base → `value_type` on `measure`, enforced at the query layer (reject/warn on cross-type aggregation).
- 12 districts missing a locale row → simply absent rows in `fact_data`; nothing to reject, charts just show "no rural data for this district" instead of a zero (important distinction — a missing row is not the same as a zero value).
- State spelling mismatch → `state_name_normalized` used for matching during upload, real `state_name` kept for display.

### 4.4 Known weaknesses, updated
- District-level `fact_data` stays small (640 districts × ~150 measures × few dataset-years × 3 locales, worst case ≈ a few hundred thousand rows) — no partitioning needed at this scope. Revisit only if subdistrict/village grain is added later.
- `value_type` enforcement is a **query-layer responsibility**, not just a database constraint — the schema alone can't stop someone from writing a bad query; Section 6's query service must actively refuse mismatched aggregations.

---

## 5. Backend Architecture (Python)

### 5.1 Service boundaries
1. **Ingestion service** — upload, parsing, column/geography matching, staging.
2. **Dataset service** — CRUD, versioning, status transitions.
3. **Analytics/query service** — the reusable core: `get_data(measure, geography_ids, locale, dataset_ids)` → tabular result, plus a small set of aggregation operations (sum, average, rank, compare) that respect `value_type`. This is the one piece of the review doc worth keeping deliberately separate from visualization — charts should call this, never touch `fact_data` directly.
4. **Auth/user service** — login, roles.

### 5.2 Stack
- **Framework:** FastAPI.
- **File parsing:** pandas.
- **Fuzzy matching:** `rapidfuzz` for column-name and state/district-name matching (handles the `&` vs `AND` case and similar).
- **Migrations:** Alembic. **ORM:** SQLAlchemy.

### 5.3 Upload pipeline (expanded, based on real gaps found)
1. **Upload** — file lands in staging, `dataset` row created with status `processing`.
2. **Profile** — read headers, sample rows, detect if the file has a locale-split structure (like the housing file) or is flat (like the district file) — check for a Rural/Urban-style column automatically.
3. **Detect schema** — for each column, fuzzy-match against `measure.key`/`display_name`; for geography columns, match against `geography.district_code` first (fast, exact), fall back to normalized name matching only if no code column exists.
4. **Validate** — type checks, range checks (0–100 for percentages, non-negative for counts), and **tolerate legitimately missing locale rows** rather than flagging them as errors (this was a real, valid pattern in the housing data, not a defect).
5. **Clean/Normalize** — strip whitespace, normalize state/district names for matching, coerce numeric types.
6. **Preview** — show the user a mapping summary + a small sample of rows as they'll be imported.
7. **Approve** — human confirms mappings (or fixes unmatched ones) — status → `pending_confirmation` until this happens.
8. **Import** — write to `fact_data`.
9. **Version** — if this is a re-upload of an existing dataset/year, create a new `dataset` version rather than overwriting.
10. **Audit** — `column_mapping` rows persist permanently as the record of how this data was interpreted.
11. **Publish** — status → `active`, now queryable and visible in the Explore view.

This is the one meaningful expansion adopted from the review pass — the extra stages (Profile, Detect Schema, Validate as distinct steps) are justified because the real housing file needed exactly this level of handling (structure detection + tolerance for missing combinations), not because "more stages" is inherently better.

### 5.4 Validation rules
- Counts: non-negative, no upper bound assumption.
- Percentages: 0–100 range, and same-locale percentages that should sum close to 100 (e.g. rural + urban ≈ total distribution checks) get flagged if wildly off — logged, not hard-rejected.
- Missing locale row: allowed, logged as "not applicable" rather than treated as an error.

---

## 6. Frontend Architecture (React)

### 6.1 Core screens
1. **Dashboard/Home** — available datasets, quick stats.
2. **Explore view** — pick measure, geography (state/district), locale, dataset/year → table + chart.
3. **Upload screen** — file picker → mapping confirmation screen → import.
4. **Dataset management** — versions, status, archive.
5. **Comparison view** — same measure across locales, districts, or dataset-years side by side.

### 6.2 Mapping confirmation screen (still the most important screen)
- Left: raw column headers + sample values.
- Right: suggested measure match (editable dropdown) + confidence indicator.
- Locale detection shown explicitly if the system detects a Rural/Urban/Total-style column, so the user confirms it rather than it being silently inferred.
- Geography match status (district code matched vs. name-matched vs. unmatched) shown per row, not just per file.
- "Confirm and Import" disabled until every column is mapped or explicitly ignored.

### 6.3 Visualization components
- Choropleth map (geography + measure + locale toggle).
- Bar chart (measure across districts/states).
- Line chart (measure across dataset-years, once more than one year is loaded).
- Sortable/filterable data table.
- All driven by the same query service response shape (Section 5.1, #3) — one data contract, many renderers. Charts render **results of an aggregation**, not raw rows — this is the one visualization-philosophy point from the review worth keeping, since it's cheap to enforce now and costly to retrofit.

### 6.4 "Live" updates
- Refetch-on-change (TanStack Query cache invalidation) after upload/import completes. No websockets in V1.

---

## 7. Build Order

| Step | What you build | Why this order |
|---|---|---|
| 1 | Confirm domain model against both reference files (Section 2 — already done) | Removes guesswork before schema work |
| 2 | Postgres schema (Section 4), manually load `india-districts-census-2011.csv` first | Simplest file (flat, no locale split) — proves the core schema |
| 3 | Query service (`get_data`) + one API endpoint | Prove the core abstraction |
| 4 | One chart (bar chart) in React | End-to-end slice, demoable |
| 5 | Explore view with measure/geography selectors | Usable product |
| 6 | Load `india_census_housing-hlpca-full.csv` manually, extending schema to use `locale` and `value_type` | Proves the harder case before building upload automation around it |
| 7 | Upload pipeline (Section 5.3) | Build against two already-understood file shapes, not blind |
| 8 | Mapping confirmation screen (Section 6.2) | Pairs with Step 7 |
| 9 | Choropleth map + comparison view | Expand visualization breadth |
| 10 | Dataset versioning + validation guardrails | Add safety once core flow is proven |
| 11 | Basic auth/roles | Needed before multi-user use |

**Key change from v1:** manually load *both* reference files (Steps 2 and 6) before building the upload pipeline, since they represent the two structurally different shapes (flat vs. locale-split, counts vs. percentages) the pipeline must handle. Building upload automation against only one shape would have missed the locale/value_type problem entirely.

---

## 8. Stress-Test Checklist (updated with real findings)

- **Locale handling:** Does a district missing its "Rural" row render as "no data" on the map, not as zero? (Must verify explicitly — this is a real, confirmed edge case, not hypothetical.)
- **Value type safety:** Can the query service be made to average a percentage-based measure with a count-based one by mistake? (Should be structurally prevented, not just documented.)
- **Geography matching:** Does the normalized state-name match correctly reconcile `"JAMMU & KASHMIR"` and `"JAMMU AND KASHMIR"` without a human needing to intervene every time? (Test this specific pair — it's a real case in hand, not a guess.)
- **Grain:** What happens if a future dataset arrives at subdistrict/village level? (Confirmed out of scope for V1 — should fail loudly with a clear "grain not supported yet" message, not silently import at the wrong level.)
- **Auditability:** Can any number on a chart be traced back to its source file, row, and mapping decision? (`column_mapping` + `dataset` version should make this possible — verify.)

---

## 9. Explicitly Deferred to Phase 2 (unchanged)

- Natural language querying / RAG chatbot
- MCP tool exposure (service boundaries in Section 5.1 are designed to make this easy later)
- Predictive analytics / forecasting / ML models
- Automated anomaly detection
- Agentic workflows
- Real-time push/websocket infrastructure
- Non-Census datasets
- Full enterprise metadata catalog (lineage/ownership/tags) — revisit only if external data providers are ever onboarded

---

## 10. Open Questions Resolved by the Reference Data

1. ~~District-level only for V1, or village-level?~~ **Resolved: district-level** — both reference files confirm this grain.
2. Which Census editions in scope for V1? Still open — both reference files are 2011-only; confirm whether 2001 comparison data will actually be sourced before building the year-comparison view.
3. Single-user or multi-user for V1? Still open — affects whether Step 11 moves earlier.
4. File storage — local disk vs. object storage? Still open, but low-stakes at current file sizes (both reference files are under 1.5MB).
