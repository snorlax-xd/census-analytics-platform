# DATABASE.md

Schema, data sourcing, and migration approach for the Census Analytics Platform. See `ARCHITECTURE.md` for how this fits into the overall system.

---

## 1. Design principle: tall/long fact table

Rather than one wide table with a column per metric, all metric data lives in a single tall table (`fact_values`): one row per `(locale, measure, year)` combination. This is what lets both tabs, and every preset query, run off one generic query shape (`filter by locale list + year, join to measure`) instead of needing bespoke logic per metric. It also means adding a new metric later is a data-insert operation, not a schema migration.

**Revised given the actual primary data source (see §2 below): `fact_values` rows at the state/UT level are not loaded directly — they are computed by aggregating district-level source rows during ETL.** The raw data is district-granular; the platform's current scope (Tab 1, Tab 2) is state/UT-granular. This is a real transformation step, not a straight import.

---

## 2. Primary data source — `india-districts-census-2011.csv`

This is the actual dataset the platform will be seeded from, so the schema and ETL plan below are written against its real shape, not an assumed one.

- **Granularity: district-level, not state-level.** 640 rows, one per district, across 35 states/UTs. State-level numbers for Tab 1's map and Tab 2's comparisons must be **aggregated** from these district rows — summed for counts, recomputed (not averaged) for rates. See §6.
- **118 columns.** Far broader than the four metrics (population, density, sex ratio, literacy rate) the original design discussion assumed. Categories present in the raw data: core demographics (population, sex, SC/ST), workforce (worker counts by type — cultivator, agricultural, household, other), religion composition, education attainment levels, age brackets, household amenities (electricity, LPG, internet, computer, vehicles, phones, TV), housing conditions (kitchen, bathing, latrine, drinking water source, household size), and household income distribution (`Power_Parity` brackets). Full column-to-category mapping is finalized in §8.
- **Data quality:** no missing values across any of the 118 columns for any of the 640 districts. District codes are unique. Sanity-checked derived literacy rate falls in a plausible 29%–89% range across districts.
- **State names are uppercase, and reflect 2011-era administrative boundaries** — this has real consequences (see §3's `locales` table notes):
  - Uses **35** states/UTs, not the current 36 — this dataset predates Telangana's creation from Andhra Pradesh (2014), predates the Jammu & Kashmir / Ladakh split (2019), and predates the merger of Dadra & Nagar Haveli with Daman & Diu into one UT (2020).
  - Uses old names for three entries: `ORISSA` (now Odisha), `PONDICHERRY` (now Puducherry), `NCT OF DELHI` (Delhi).
- **No geometry.** This CSV has no boundary/shape data — boundary GeoJSON is still sourced separately (§5), and per the point above, **must be sourced at the same 2011-era boundary vintage** (undivided Andhra Pradesh, undivided Jammu & Kashmir, undivided Dadra & Nagar Haveli and Daman & Diu) so the map's regions line up 1:1 with what this data can actually report. Rendering current (post-2014/2019/2020) state boundaries against this data would either leave Telangana/Ladakh with no data or force duplicating the undivided parent's value into both pieces, which is misleading. **Decision: Tab 1 and Tab 2 render 2011-era state/UT boundaries, matching the data, not the current 36-region map.** This should be stated on-screen alongside the existing "Data as of Census 2011" label so it reads as one coherent vintage, not two separate caveats.

---

## 3. Tables

### `locales`
One row per state or Union Territory, **at 2011-era boundaries** (35 rows — see §2).

| Column | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `iso_code` | string(4), unique, indexed | ISO 3166-2:IN code, e.g. `MH`, `GJ`. For the three renamed entries, use the current standard code (Odisha → `OD`, Puducherry → `PY`, Delhi → `DL`) even though the source CSV spells the name the old way — the raw `State name` column is a source-data quirk to normalize during ETL, not something that should leak into the app's labeling. |
| `name` | string(100) | current standard name, e.g. "Odisha" not "Orissa" — same reasoning as above |
| `source_name` | string(100) | the raw `State name` value exactly as it appears in the CSV (e.g. `"ORISSA"`), kept for traceability back to the source file and to make the ETL join deterministic and auditable |
| `type` | string(10) | `"state"` or `"ut"` |
| `centroid_lat`, `centroid_lng` | float | used for map label placement / quick-zoom shortcuts |
| `area_sq_km` | float, nullable | **Not present in the primary CSV** (`india-districts-census-2011.csv` has no area/km² column at all — verified, see §8). Required to compute `population_density`, one of the four metrics originally assumed for Tab 1's default metric list. Must be sourced separately as a small static supplementary table (2011-era state land areas — a stable, well-documented public figure, easy to source once from official Census 2011 area tables even though it's absent from this particular file) and loaded onto `locales` directly, not into `fact_values`, since it isn't itself a year-varying census measure in this dataset's scope. **Until this is sourced, `population_density` cannot be built — pull it from Tab 1's v1 metric list, or add the area table before Phase 4.**

A small **state name-mapping table** (or a hardcoded dict in the seed script — a database table is overkill for 3 exceptions) is needed to normalize `ORISSA`→Odisha, `PONDICHERRY`→Puducherry, `NCT OF DELHI`→Delhi during ETL. Every other state name in the source matches its current name exactly.

### `districts` *(new — required by the actual data granularity)*
One row per district, as it exists in the source data.

| Column | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `source_district_code` | integer, unique, indexed | the `District code` column from the CSV |
| `name` | string(100) | the `District name` column |
| `locale_id` | FK → `locales.id` | which state/UT this district belongs to |

This table exists so district-level source data has a proper home and an audit trail back to the CSV — **not** to power a district-level UI feature right now (that's an explicit future item, see `ROADMAP.md`/`DESIGN.md`'s Tab 1 out-of-scope notes on drill-down). For the current scope, it is read only by the aggregation step in §6.

### `measures`
One row per metric definition.

| Column | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `code` | string(50), unique, indexed | e.g. `literacy_rate`, `population`, `sex_ratio` |
| `name` | string(100) | display name, e.g. "Literacy Rate" |
| `unit` | string(30) | e.g. `%`, `people`, `per km2` |
| `category` | string(50) | one of: `demographics`, `economy`, `literacy`, `infrastructure`, `sanitation`, `drinking_water` — drives Tab 2's category sidebar. Finalized in §8 — `health` was dropped (no supporting source data) in favor of splitting sanitation and drinking water into their own dedicated categories, since the source data is granular enough on both to justify it. |
| `higher_is_better` | boolean, nullable | `true` = higher is better (literacy rate), `false` = lower is better, `null` = non-directional (population, area). **Required** — the Tab 2 verdict card and ranking badges cannot function without this being set correctly for every measure. |
| `is_derived` | boolean | *(new)* `true` if computed during ETL from raw source columns (e.g. `literacy_rate = Literate / Population`), `false` if loaded directly from a single source column (e.g. `population`). Documents provenance so it's clear which measures can be recomputed if the source data changes and which are stored as-is. |

### `fact_values`
The tall fact table — the single source of truth for every number shown on either tab. **Holds state/UT-level values only** (post-aggregation) — district-level raw values are not stored here, they live implicitly in the source CSV and are re-derived by the ETL step whenever it runs (see §6).

| Column | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `locale_id` | FK → `locales.id` | |
| `measure_id` | FK → `measures.id` | |
| `year` | integer | `2011` for all current data; schema already supports other years without change |
| `value` | float | |

Constraint: `UNIQUE(locale_id, measure_id, year)` — one value per locale/measure/year combination, no duplicates.

**Indexing note:** add an index on `(measure_id, year, value)` — this is what makes the Tab 2 "closest state by metric" preset query (an `ORDER BY ABS(value - anchor_value)` sort) and the national ranking computation (`RANK() OVER (PARTITION BY measure_id, year ORDER BY value DESC)`) efficient as the dataset grows. Not strictly necessary at current data volume (35 locales), but cheap to add now.

### `state_adjacency`
Static reference table for Tab 2's "Neighboring State" preset. Populated once from official boundary data (at the same 2011-era vintage as everything else, per §2), not derived at query time.

| Column | Type | Notes |
|---|---|---|
| `id` | integer, PK | |
| `state_code` | string(4), indexed | |
| `neighbor_code` | string(4) | |
| `shared_border_length` | float | used to pick the best neighbor when a state has several — longest shared border wins, not an unrelated metric like population |

**Implementation note (as of Phase 2):** the spec above calls for this table to be derived from real boundary geometry. Since no boundary GeoJSON exists in the repo yet (it's sourced in Phase 4, see §7), the current seed script populates this table from a hand-curated static list instead, with `shared_border_length` values assigned as relative priority rather than measured lengths. This already caused one real bug (an enclave state briefly outranking an actual neighbor for Maharashtra) that had to be patched by hand. **Once boundary GeoJSON is sourced in Phase 4, recompute this table from real geometry and replace the hand-curated version** — don't let this stopgap become permanent by default.

Island states (Andaman & Nicobar, Lakshadweep) have no rows in this table where they are `state_code` — the preset endpoint returns a null result for them, and the frontend disables the "Neighboring State" preset button with a tooltip rather than treating this as an error.

---

## 4. Migrations

All schema changes go through Alembic (`alembic revision --autogenerate -m "description"`, then `alembic upgrade head`). Never modify the schema with a manual `ALTER TABLE` outside of a tracked migration — this is what keeps the schema reproducible across environments and reversible if a change turns out to be wrong.

---

## 5. Data sourcing

- **Metric data**: `india-districts-census-2011.csv` (district-level, 2011) — see §2 for its actual shape and caveats. This is the confirmed primary source, replacing the earlier vague reference to "official Census tables."
- **Boundary/GeoJSON data**: still sourced separately from Survey of India or the Census of India's own GIS shapefiles — the CSV has no geometry. **Must be the 2011-era boundary vintage** (§2) to stay consistent with this data. A single authoritative source is used for both the national and focused-state map views, to avoid border mismatches that come from mixing sources.
- **State adjacency data**: derived once from that same boundary source, at the same 2011-era vintage.

Do not substitute a convenient third-party GeoJSON npm package, and do not substitute a current-boundary (36-region) map — either would silently break the 1:1 match with this CSV.

---

## 6. ETL: from district rows to state-level facts

This replaces the earlier, simpler description of the seed script — the actual transformation has three real steps, not one:

1. **Load and normalize.** Read the CSV, apply the state name-mapping (§3) to resolve `ORISSA`/`PONDICHERRY`/`NCT OF DELHI` to their current names/codes, insert one row per district into `districts`, linked to the correct `locales` row.
2. **Aggregate to state level.** For each state/UT, aggregate its district rows:
   - **Count-type measures** (population, literate count, worker count, households with electricity, etc.): summed across districts.
   - **Rate-type measures** (literacy rate, sex ratio, worker participation rate, etc.): **recomputed from the summed counts, never averaged across districts.** E.g. state literacy rate = `SUM(district Literate) / SUM(district Population)`, not the mean of each district's individual literacy rate — averaging rates directly would silently misweight small and large districts equally, which is a real and easy-to-miss correctness bug.
3. **Derive rate measures and insert.** Compute every `is_derived = true` measure (§3) from the aggregated counts, and insert both the raw aggregated counts and the derived rates into `fact_values` as separate `measures` rows where both are independently useful (e.g. `population` as a raw count feeds Tab 2's per-capita toggle math directly, while `literacy_rate` is the derived percentage shown by default).

This script (`backend/scripts/seed.py`, Phase 1) is a one-off/re-runnable script, not application code that runs on every startup.

---

## 7. Boundary data preprocessing

The raw official boundary data (2011-era vintage, §2/§5) is simplified once, offline, via `mapshaper` into two static files:
- A simplified version (far fewer coordinate points) for the national zoomed-out view.
- The full-detail version, loaded only when a user clicks into a specific state's focused view.

This preprocessing step happens outside the running application — it's a build-time/data-prep task, not something computed live in the browser or the API.

---

## 8. Finalized v1 column selection

Resolved per your direction: no forced-fit `health` category — sanitation and drinking water get their own dedicated categories instead, sourced directly from the columns the dataset actually provides.

**Categories with a clear column mapping in the source data:**
- **Demographics** — `Population`, `Male`/`Female` (→ `sex_ratio` derived), `SC`/`ST` counts (→ percentage of population), age group breakdown (`Age_Group_0_29`, `_30_49`, `_50`).
- **Literacy** — `Literate`, `Male_Literate`/`Female_Literate` (→ derived rates), education attainment levels (`Below_Primary` through `Graduate_Education`).
- **Economy** — `Workers` and its subtypes (`Cultivator_Workers`, `Agricultural_Workers`, `Household_Workers`, `Other_Workers`) → worker participation rate and workforce composition; `Power_Parity_*` income brackets → household income distribution, a genuinely useful proxy given there's no GDP figure in this dataset.
- **Infrastructure** — household amenities (`LPG_or_PNG_Households`, `Housholds_with_Electric_Lighting`, `_Internet`, `_Computer`, `_Television`, vehicle/phone ownership) and housing/sanitation (drinking water source, latrine facility, bathing facility).

**Categories with no clear column mapping — resolved:**
- **`health`** is dropped as a category. The source data has no mortality/morbidity/hospital-access columns to support it. **Decision: sanitation and drinking water each become their own dedicated category**, rather than being folded into a repurposed `health` label or a generic `infrastructure` catch-all — the source data is granular enough on both to justify separate treatment:
  - **`sanitation`** — `Condition_of_occupied_census_houses_Dilapidated_Households`, `Households_with_separate_kitchen_Cooking_inside_house`, `Having_bathing_facility_Total_Households`, `Having_latrine_facility_within_the_premises_Total_Households`, `Type_of_bathing_facility_Enclosure_without_roof_Households`, the four `Type_of_latrine_facility_*` columns (pit, other, night-soil-to-open-drain, flush-connected), `Not_having_bathing_facility_within_the_premises_Total_Households`, `Not_having_latrine_facility_within_the_premises_Alternative_source_Open_Households`.
  - **`drinking_water`** — the `Main_source_of_drinking_water_*` columns (covered well, handpump/tubewell/borewell, spring, river/canal, tank/pond/lake, tapwater, tubewell/borehole, other) and the `Location_of_drinking_water_source_*` columns (near/within/away from premises).
  - `Type_of_fuel_used_for_cooking_Any_other_Households` doesn't cleanly fit either new category or `infrastructure` — leave unassigned/deferred rather than forcing a placement.
- The **final v1 category list is: `demographics`, `economy`, `literacy`, `infrastructure`, `sanitation`, `drinking_water`** — six categories, not the original five. `DESIGN.md`'s Tab 2 sidebar (§B.5) should be updated to match.

**Separately — a gap unrelated to categories, caught in this same pass:** the primary CSV has **no area/km² column of any kind**, confirmed by checking every column name. `population_density` was one of Tab 1's four originally-assumed default metrics (`DESIGN.md` §A.2) and cannot be built from this file alone — see the `area_sq_km` note on `locales` above (§3). Resolve by either sourcing a small supplementary state-area table before Phase 4, or dropping `population_density` from the v1 metric list and adding it later. Don't let this surface as a silent bug (e.g. a metric option that 500s when selected) — decide one way explicitly.

**Still deferred (unchanged from before):**
- **Religion composition** (`Hindus`, `Muslims`, `Christians`, `Sikhs`, `Buddhists`, `Jains`, `Others_Religions`) — present in the source data but not part of any category above. Worth a deliberate decision rather than a default include/exclude: presentable neutrally (a simple percentage breakdown, no framing or ranking language) if included, but changes the platform's scope in a way worth confirming intentionally rather than defaulting either way.
- **Household size / marital composition** (`Household_size_*`, `Married_couples_*`) — granular household-structure data with no obvious category home in the current six-category list; likely lower priority for v1 regardless of category placement.

**Phase 1 is now unblocked** on the category question — the remaining open items above (religion, household structure) are lower-priority and don't block finalizing the v1 measure list.


---

## 9. Future extension (not built yet, but the schema anticipates it)

- **Multi-year data**: the `year` column on `fact_values` already supports this — adding a second census year is a data-load operation, not a schema change.
- **District-level drill-down**: the new `districts` table (§3) already holds the necessary source data — a future feature could expose district-level detail within a focused state view without a schema change, only new aggregation logic and UI.
- **RBAC tables** (`users`, `roles`, `role_permissions`, `audit_log`): described fully in `RBAC.md`, not created until Phase 7.
