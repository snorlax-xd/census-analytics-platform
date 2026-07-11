# Census Analytics Platform — Development Plan (v3)

**Scope:** Census-related datasets only (Census 2011 as seed, 2026 Census to be added later as a new dataset/year)
**Stack:** React (frontend) · Python/FastAPI (backend) · PostgreSQL (database)
**Phase:** V1 foundation, single-user, architected so multi-user scaling later doesn't require a redesign. AI/RAG/NL-querying deferred to Phase 2.
**Reference datasets validating this plan:** `india-districts-census-2011.csv` (flat, district-grain, counts), `india_census_housing-hlpca-full.csv` (locale-split, district-grain, percentages)

---

## 1. Guiding Principles

1. **One domain, understood deeply** — Census-shaped data only: geography-indexed, demographic, tabular, batch-updated.
2. **Grain and geography are the spine.** Every query reduces to: which measure, at which geography, for which locale/year/dataset.
3. **Human confirms, system suggests.** No AI in V1.
4. **Simple before clever.** One fact table, not one table per dataset. Refetch-on-change, not websockets.
5. **Never silently guess or silently drop.** Unmatched data is surfaced, not assumed.
6. **Build single-user, leave seams for multi-user.** Don't build auth/roles complexity now — but don't hardcode single-user assumptions into the data model either (see Section 8).

---

## 2. Resolved Open Questions

| Question | Decision |
|---|---|
| Census editions in scope | 2011 now. Architecture must cleanly accommodate 2026 Census as a new `dataset` row (new year, possibly new/renamed measures) without a redesign — this is already handled by the `dataset`/`measure` table design (Section 5), not a special case. |
| Single vs multi-user | Single-user for V1. `users` table and `uploaded_by`/`role` fields exist in the schema now so multi-user is a permissions/auth layer added later, not a schema migration. |
| File storage | Local disk for V1, behind a storage abstraction (Section 7.4) so swapping to S3-compatible storage later is a config change, not a rewrite. Files stored per-dataset-id to avoid future collisions when 2026 data arrives. |

---

## 3. What the Reference Datasets Confirmed

| Finding | Detail | Design implication |
|---|---|---|
| Both files are district-grain | 640 districts, 35 states, in both | District-level confirmed as V1 grain |
| District code is a reliable join key | Codes 1–640 identical across both files | `district_code` is the canonical geography ID |
| State name spelling differs | `"JAMMU & KASHMIR"` vs `"JAMMU AND KASHMIR"` | Name-normalization step still needed even on clean data |
| Housing file has an extra dimension | 3 rows/district: Rural / Urban / Total | Need a `locale` dimension, not just geography + measure |
| Housing file values are percentages | e.g. "Total Number of households" = 100 in every row | Need `value_type` (`count`/`percentage`) per measure |
| 12 districts missing a locale row | e.g. fully urban districts have no "Rural" row | Import must tolerate legitimately missing rows |

---

## 4. Domain Model

### 4.1 Geography
```
Country → State → District
```
District-level only for V1 (both files confirm this grain; subdistrict/village deferred).

### 4.2 Four-part data shape
Every value = **Geography** × **Measure** × **Locale** (`rural`/`urban`/`total`) × **Dataset/Year**.

### 4.3 Measures
Fixed, versioned vocabulary, each tagged `value_type` (`count` or `percentage`). Never aggregate across types without explicit conversion.

---

## 5. Database Schema (PostgreSQL)

```sql
-- geography: one row per district
CREATE TABLE geography (
    id                      SERIAL PRIMARY KEY,
    district_code           INTEGER NOT NULL UNIQUE,
    district_name           TEXT NOT NULL,
    state_name              TEXT NOT NULL,
    state_name_normalized   TEXT NOT NULL,   -- lowercase, punctuation-stripped
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_geography_state_normalized ON geography (state_name_normalized);

-- dataset: one row per uploaded file/version
CREATE TABLE dataset (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    year            INTEGER NOT NULL,
    source          TEXT,
    status          TEXT NOT NULL CHECK (status IN ('processing','pending_confirmation','active','archived','failed')),
    file_storage_key TEXT NOT NULL,          -- see storage abstraction, Section 7.4
    version         INTEGER NOT NULL DEFAULT 1,
    uploaded_by     INTEGER REFERENCES users(id),  -- nullable in single-user V1
    uploaded_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_dataset_year_status ON dataset (year, status);

-- measure: fixed vocabulary, extensible without migration
CREATE TABLE measure (
    id              SERIAL PRIMARY KEY,
    key             TEXT NOT NULL UNIQUE,     -- e.g. 'literacy_rate'
    display_name    TEXT NOT NULL,
    value_type      TEXT NOT NULL CHECK (value_type IN ('count','percentage')),
    unit            TEXT
);

-- fact_data: the core tall table
CREATE TABLE fact_data (
    id              BIGSERIAL PRIMARY KEY,
    dataset_id      INTEGER NOT NULL REFERENCES dataset(id),
    geography_id    INTEGER NOT NULL REFERENCES geography(id),
    measure_id      INTEGER NOT NULL REFERENCES measure(id),
    locale          TEXT NOT NULL DEFAULT 'total' CHECK (locale IN ('rural','urban','total')),
    value           NUMERIC NOT NULL
);
CREATE UNIQUE INDEX idx_fact_unique ON fact_data (dataset_id, geography_id, measure_id, locale);
CREATE INDEX idx_fact_query_path ON fact_data (measure_id, geography_id, locale);

-- column_mapping: upload audit trail
CREATE TABLE column_mapping (
    id                  SERIAL PRIMARY KEY,
    dataset_id          INTEGER NOT NULL REFERENCES dataset(id),
    source_column_name  TEXT NOT NULL,
    mapped_measure_id   INTEGER REFERENCES measure(id),
    confirmed_by_user   BOOLEAN NOT NULL DEFAULT false
);

-- users: minimal now, ready for multi-user later
CREATE TABLE users (
    id      SERIAL PRIMARY KEY,
    email   TEXT UNIQUE,
    role    TEXT NOT NULL DEFAULT 'admin' CHECK (role IN ('admin','analyst','viewer'))
);
```

**Why `idx_fact_unique` matters:** it structurally prevents the same measure/locale/geography from being double-imported into one dataset — a real integrity guarantee, not just convention.

---

## 6. Backend Project Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI app instantiation, router registration
│   ├── config.py                  # Pydantic Settings — env vars, DB URL, storage path
│   ├── database.py                # SQLAlchemy engine, session factory, get_db() dependency
│   │
│   ├── models/                    # SQLAlchemy ORM models (mirrors Section 5 schema)
│   │   ├── geography.py
│   │   ├── dataset.py
│   │   ├── measure.py
│   │   ├── fact_data.py
│   │   ├── column_mapping.py
│   │   └── user.py
│   │
│   ├── schemas/                   # Pydantic request/response models (API contracts)
│   │   ├── dataset.py
│   │   ├── query.py
│   │   ├── mapping.py
│   │   └── geography.py
│   │
│   ├── services/                  # Business logic — this is where the real work happens
│   │   ├── ingestion_service.py   # upload, profile, detect schema, validate, clean
│   │   ├── mapping_service.py     # fuzzy matching, mapping confirmation logic
│   │   ├── dataset_service.py     # CRUD, versioning, status transitions
│   │   ├── query_service.py       # get_data(), aggregation, comparison — the analytics core
│   │   └── storage_service.py     # file save/read abstraction (Section 7.4)
│   │
│   ├── api/                       # Route definitions only — thin, delegate to services
│   │   └── v1/
│   │       ├── datasets.py
│   │       ├── geography.py
│   │       ├── measures.py
│   │       ├── query.py
│   │       └── mappings.py
│   │
│   └── core/
│       ├── exceptions.py          # custom exception classes
│       └── error_handlers.py      # maps exceptions to consistent HTTP error responses
│
├── alembic/                       # DB migrations
├── tests/
├── scripts/
│   └── load_reference_data.py     # one-off script to load the two reference CSVs directly (Step 2/6 of build order)
├── requirements.txt
└── .env.example
```

**Key rule: routes never touch the database or pandas directly.** `api/v1/*.py` only validates the request shape and calls a service function. This is what keeps the analytics/query logic reusable later (CLI scripts, background jobs, eventually MCP tools all call the same `services/` layer).

---

## 7. API Design

### 7.1 Conventions
- Base path: `/api/v1/`
- REST, resource-oriented, JSON in/out.
- Every error response has the same shape:
```json
{ "error": { "code": "MEASURE_NOT_FOUND", "message": "No measure with key 'foo_bar'", "details": {} } }
```
- Every list response is paginated (even though V1 data is small — cheap to do now, painful to retrofit once frontend assumes non-paginated lists):
```json
{ "items": [ ... ], "total": 640, "page": 1, "page_size": 50 }
```

### 7.2 Endpoints

**Datasets**
```
GET    /api/v1/datasets                  # list datasets (filter by year, status)
GET    /api/v1/datasets/{id}             # dataset detail + version history
POST   /api/v1/datasets                  # upload a new file → creates dataset (status=processing)
GET    /api/v1/datasets/{id}/preview     # sample rows + suggested mappings (after profiling)
POST   /api/v1/datasets/{id}/confirm     # submit confirmed column_mapping → triggers import
DELETE /api/v1/datasets/{id}             # archive (soft delete — status='archived', never hard-delete)
```

**Geography**
```
GET    /api/v1/geography/states                    # list states
GET    /api/v1/geography/districts?state_id=       # list districts, optionally filtered
```

**Measures**
```
GET    /api/v1/measures                  # list all measures (key, display_name, value_type, unit)
```

**Query / Analytics (the core endpoint)**
```
POST   /api/v1/query
```
Request body:
```json
{
  "measure_key": "literacy_rate",
  "geography_ids": [1, 2, 3],
  "locale": "total",
  "dataset_ids": [1],
  "aggregation": "none"
}
```
Response body:
```json
{
  "measure": { "key": "literacy_rate", "value_type": "percentage", "unit": "%" },
  "results": [
    { "geography_id": 1, "district_name": "Kupwara", "state_name": "Jammu and Kashmir", "dataset_id": 1, "year": 2011, "locale": "total", "value": 60.9 }
  ]
}
```
`aggregation` accepts `none | sum | avg | rank`. The service layer (`query_service.py`) rejects `sum`/`avg` requests that mix measures of different `value_type` — this is the structural enforcement point discussed in Section 5.

**Mappings**
```
GET    /api/v1/datasets/{id}/mappings           # current mapping state for a dataset
PATCH  /api/v1/datasets/{id}/mappings/{mapping_id}   # user overrides a single column's mapped measure
```

### 7.3 Why this shape scales later
- `/query` as one flexible POST endpoint (not one GET route per chart type) means new visualizations in the frontend never require new backend endpoints — they just send different query parameters. This is also exactly the shape an LLM would need to call in Phase 2 (NL query → this same JSON body), so no redesign needed then either.
- Versioned base path (`/api/v1/`) means Phase 2 additions (e.g. `/api/v1/predict`, `/api/v1/chat`) slot in alongside without breaking existing routes.

### 7.4 Storage abstraction
```python
# services/storage_service.py
def save_upload(file_bytes: bytes, dataset_id: int, filename: str) -> str:
    """Returns a storage key/path. Local disk now; swap internals for S3 later."""
    path = f"uploads/dataset_{dataset_id}/{filename}"
    # write to local disk under settings.STORAGE_ROOT
    return path

def read_upload(storage_key: str) -> bytes:
    """Reads bytes given a storage key. Same signature regardless of backend."""
    ...
```
Nothing outside this module knows whether files live on disk or in S3 — `ingestion_service.py` only calls these two functions.

---

## 8. Designing for Multi-User Without Building It Yet

Don't build login/permissions UI now. Do keep these seams open, since retrofitting them is expensive:
- `dataset.uploaded_by` and `users.role` columns exist in the schema from day one (nullable/defaulted for single-user).
- Service functions accept an optional `current_user` parameter even if V1 always passes a hardcoded default user — this avoids threading auth through every function signature later.
- No business logic assumes "there is only one of anything" (e.g. don't hardcode "the current dataset" as a global — always pass `dataset_id` explicitly).

---

## 9. Frontend Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.ts              # thin wrapper around fetch/axios, one function per endpoint
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Explore.tsx
│   │   ├── Upload.tsx
│   │   ├── MappingConfirmation.tsx
│   │   └── DatasetManagement.tsx
│   ├── components/
│   │   ├── charts/
│   │   │   ├── ChoroplethMap.tsx
│   │   │   ├── BarChart.tsx
│   │   │   └── LineChart.tsx
│   │   ├── DataTable.tsx
│   │   └── MeasureSelector.tsx
│   ├── hooks/
│   │   └── useQuery.ts            # TanStack Query wrapper around POST /query
│   └── types/
│       └── api.ts                 # TypeScript types mirroring backend Pydantic schemas
```

All chart components take the **same** query-response shape (Section 7.2) as props — new chart types are new renderers, not new data-fetching logic.

---

## 10. Build Order

| Step | What you build |
|---|---|
| 1 | Postgres schema (Section 5) via Alembic migration |
| 2 | `scripts/load_reference_data.py` — load `india-districts-census-2011.csv` directly (flat file, proves core schema) |
| 3 | `query_service.py` + `POST /api/v1/query` endpoint |
| 4 | One React chart (bar chart) consuming that endpoint |
| 5 | Explore page with measure/geography selectors |
| 6 | Extend `load_reference_data.py` to load `india_census_housing-hlpca-full.csv`, exercising `locale`/`value_type` |
| 7 | `ingestion_service.py` + upload endpoints (Section 7.2) |
| 8 | Mapping confirmation page |
| 9 | Choropleth map + comparison view |
| 10 | Dataset versioning + validation guardrails end-to-end |
| 11 | Auth (only when actually needed — seams already in place from Section 8) |

---

## 11. Stress-Test Checklist

- Does a district missing its "Rural" row render as "no data," not zero, on every chart type?
- Does `query_service` structurally reject mixed `value_type` aggregation, or just document the rule?
- Does normalized state-name matching correctly reconcile `"JAMMU & KASHMIR"` and `"JAMMU AND KASHMIR"`?
- Can 2026 Census data be added as a new `dataset` row without any schema migration? (Should be yes by construction — verify when it actually arrives.)
- Can every value in `fact_data` be traced back to its source file/row via `column_mapping`?

---

## 12. Explicitly Deferred to Phase 2

- Natural language querying / RAG chatbot
- MCP tool exposure (service-layer boundaries in Section 6 designed to make this a thin wrapper later)
- Predictive analytics / forecasting / ML
- Automated anomaly detection
- Agentic workflows
- Real-time push/websocket infrastructure
- Non-Census datasets
- Full multi-user auth/permissions UI (seams only, per Section 8)
