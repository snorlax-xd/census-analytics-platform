# API.md

Endpoint contracts for the Census Analytics Platform backend. See `DATABASE.md` for the underlying schema and `ARCHITECTURE.md` for why the endpoint set is shaped this way.

---

## Base URL (local dev)

`http://localhost:8000`

CORS is enabled for the Vite dev server origin (`http://localhost:5173`) in `main.py`. If the frontend dev port changes, update `allow_origins` accordingly.

---

## `GET /api/v1/analytics`

The single flexible endpoint used by both tabs.

**Query parameters**

| Param | Type | Required | Notes |
|---|---|---|---|
| `states` | string | yes | Comma-separated ISO codes, e.g. `MH,GJ`. Tab 1's focused view sends one code; Tab 2 sends two. Not capped at the API level — a future 3+ state feature is a frontend-only change. |
| `year` | integer | no, default `2011` | Only `2011` has data currently. |
| `include_rank` | boolean | no, default `false` | When `true`, each measure includes its national rank for that year (used by Tab 2's ranking badges). |

**Response shape**

```json
{
  "data": [
    {
      "locale_code": "MH",
      "locale_name": "Maharashtra",
      "year": 2011,
      "measures": [
        {
          "measure_code": "literacy_rate",
          "measure_name": "Literacy Rate",
          "category": "literacy",
          "unit": "%",
          "value": 82.3,
          "higher_is_better": true,
          "rank": 5
        }
      ]
    }
  ]
}
```

`rank` is `null` unless `include_rank=true` was passed. `higher_is_better` is `null` for non-directional measures (e.g. population) — the frontend must handle this case rather than assuming every measure has a direction (see `DESIGN.md` §6.8.1–6.8.2).

---

## `GET /api/v1/presets/closest`

Tab 2's numeric presets ("Similar Literacy," "Similar Population," etc.) — finds the single state whose value on a given measure is closest to the anchor state's.

**Query parameters**

| Param | Type | Required |
|---|---|---|
| `anchor` | string | yes — ISO code of State A |
| `metric` | string | yes — measure code, e.g. `literacy_rate` |
| `year` | integer | no, default `2011` |

**Response**

```json
{ "state_code": "GJ", "state_name": "Gujarat", "value": 78.0 }
```

**Behavior notes**
- Always excludes the anchor state itself from the candidate pool.
- Excludes states/UTs with no recorded value for the given measure (does not treat a missing value as zero).
- Resolution is a single `ORDER BY ABS(value - anchor_value) LIMIT 1` query — there is no top-N slicing or tie-breaking logic, since exactly one result is needed (per the fixed two-state model in `DESIGN.md`).
- Returns `404` if the anchor state or metric code doesn't exist, or if the anchor itself has no data for that metric.

---

## `GET /api/v1/presets/neighbor`

Tab 2's "Neighboring State" preset.

**Query parameters**

| Param | Type | Required |
|---|---|---|
| `anchor` | string | yes — ISO code of State A |

**Response**

```json
{ "state_code": "GJ", "state_name": "Gujarat" }
```

**Behavior notes**
- If the anchor has multiple neighbors, returns the one with the longest shared border (from `state_adjacency.shared_border_length`) — not selected by population or any unrelated metric.
- If the anchor is an island state with no land border (Andaman & Nicobar, Lakshadweep), returns `{ "state_code": null }`. This is not an error — the frontend must interpret a null `state_code` as "disable this preset button with a tooltip," not surface it as a failed request.

---

## Error handling conventions

- `404` for "the requested state/measure doesn't exist" or "no data available for this combination" — always with a `detail` message explaining which.
- Do not return `200` with an empty/null payload where a `404` is more accurate — the frontend's preset-disabling logic (§ above) depends on being able to distinguish "no neighbor exists" (a valid `200` with `state_code: null`) from "the anchor state itself doesn't exist" (a `404`).

---

## Not yet built (Phase 7)

Authentication and any write endpoints (data upload, measure editing, publishing a data version) are documented in `RBAC.md` and are not part of the current API surface. Both endpoints above are public, unauthenticated, read-only — this is intentional, not a placeholder to "fix" early.
