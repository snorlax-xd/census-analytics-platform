# SESSION HANDOFF — Census Analytics Platform

Continuation document for a new conversation. Read this first, in full, before doing anything else.

---

## 1. What this project is

A two-tab web platform for exploring/comparing Indian Census 2011 data.
- **Tab 1**: interactive national map of India, colored by a selectable metric, click-through to a focused state view.
- **Tab 2**: fixed two-state side-by-side comparison with charts, presets, scorecards.

Stack: **React (Vite) + FastAPI + PostgreSQL**.

Repo root: `C:\Users\Lenovo\Desktop\Census Analytics Platform`
Folders: `Backend/`, `Frontend/` (on-disk casing has been inconsistent — `cd frontend` lowercase has worked fine since Windows paths are case-insensitive; don't worry about this).

---

## 2. The nine core spec files (attach these to the new conversation)

These are the authoritative source of truth for the whole build. All nine already exist in the repo root:

1. **AGENTS.md** — entry point; build order, conventions, non-negotiable decisions
2. **ARCHITECTURE.md** — stack, folder structure, data flow
3. **DATABASE.md** — schema, the real dataset's actual shape, district→state ETL, boundary vintage decisions
4. **API.md** — exact endpoint contracts
5. **DESIGN.md** — full UX/interaction spec for both tabs (supersedes the two tab-specific files below for anything they conflict on)
6. **SKILLS.md** — step-by-step patterns for recurring dev tasks
7. **ROADMAP.md** — phase-by-phase build order
8. **tab1_national_map_explorer_spec.md** — original detailed Tab 1 design discussion (background only)
9. **tab2_state_comparison_engine_spec.md** — original detailed Tab 2 design discussion (background only)

Also exists but **not needed yet**: **RBAC.md** (deferred to Phase 7, no curation flow exists yet — don't attach unless starting that phase).

Two more working documents, also exist in repo root:
- **RUNBOOK.md** — environment gotchas (Windows `py` vs `python`, Docker cold-start, Tailwind `spawn EPERM`, venv `ensurepip` permission errors), git workflow, command-approval guidance.
- **PHASE4_PROMPT_SEQUENCE.md** — the six-prompt breakdown for Tab 1's build (see §6 below — **two of these prompts need updating**).

**Attach all of the above except RBAC.md to the new conversation, plus this handoff document itself.**

---

## 3. Current status: Phases 0–3 complete and verified

Verified numbers as of last check:
- `locales`: 35 (2011-era boundaries — undivided Andhra Pradesh, undivided Jammu & Kashmir, Dadra & Nagar Haveli and Daman & Diu still separate — NOT the current 36-region India)
- `districts`: 640
- `measures`: 32 (`population_density` deliberately excluded — no area/km² column exists in the source CSV)
- `fact_values`: 1120
- `state_adjacency`: 126 rows (used by the `/presets/neighbor` endpoint)
- Alembic: migrated to head
- Backend: `GET /api/v1/analytics`, `GET /api/v1/presets/closest`, `GET /api/v1/presets/neighbor` all implemented and tested working
- Frontend: routing (`/tab1`, `/tab1/state/:id`, `/tab2`) and React Query wired, confirmed hitting the live backend

**Primary data source**: `Database/india-districts-census-2011.csv` (district-level, not state-level — state numbers are aggregated in the seed script, never sourced directly).

---

## 4. Git status

A git repo exists (`git init` was run manually partway through). Known commits include:
- Initial Phase 0–3 scaffold
- `19f5a3b` — boundary GeoJSON (simplified + full detail) — **this specific commit's files are now STALE and will be overwritten once the fix in §7 is applied**
- The `.gitignore` had a serious bug at one point (`*.md` / `!README.md` excluded ALL spec docs from git, including `AGENTS.md` etc.) — this should have been fixed; **verify with `git check-ignore -v AGENTS.md DATABASE.md DESIGN.md`** in the new session before assuming docs are tracked.
- `prepare_boundaries.py` may or may not be committed yet — check `git status`.

**First thing to do in the new session**: run `git status` and `git log --oneline` and confirm the state matches expectations above before proceeding.

---

## 5. Codex status

**Codex is out of usage** (reset message showed a date around Aug 10, 2026 — check your actual account/plan page, this may be shorter than it appeared). Until it's available again, **all execution is being done manually by the user**, with Claude giving exact, single-line, copy-paste-ready commands and code, one step at a time, verified via pasted terminal output and screenshots before proceeding.

**Lessons learned from this manual workflow, apply going forward**:
- **Always use an explicit `Set-Location` to the repo root at the start of any command sequence.** Different terminal tabs have independent working directories — a `cd ..` in one tab does not relate to another tab's location. This caused two separate failures in this session.
- **Never use PowerShell backtick (`` ` ``) line continuations for multi-line commands** — copy-paste corrupts them unpredictably (e.g. `format=geojson` got truncated to `format=geojs` this way). Give every command as a single unbroken line.
- **Vite's default JSON import only recognizes the `.json` extension**, not `.geojson` — this caused a real bug. Boundary files are now output directly as `.json` (`india-simplified.json`, `india-full-detail.json`), not `.geojson`.

---

## 6. Tab 1 build status — Phase 4, Prompt 1 (static map render)

This is the current, unfinished piece. Long debugging chain, now understood:

1. **Boundary data pipeline built**: `Backend/scripts/prepare_boundaries.py` downloads 2011 Census district boundaries (source: `yashveeeeeeer/india-geodata` GitHub release, `Districts_2011.geojsonl.7z`), maps numeric census codes (`01`–`35`) to state names via a verified lookup table, dissolves districts into 35 state-level polygons, and — critically — applies `shapely.geometry.polygon.orient()` to fix polygon winding order (Shapely's `unary_union()` produces OGC/clockwise-exterior winding; GeoJSON/d3-geo require RFC7946/counter-clockwise-exterior winding — mismatched winding causes polygons to render "inside-out"). Full current content of this script is in Appendix A.
2. **This script has a mandatory two-pass safety design**: dry-run (default, prints a table of proposed name + centroid per region for manual verification) and `--write` (actually produces output). This exists because the source data's state field turned out to be numeric codes, and a silent wrong mapping would have mislabeled every region downstream.
3. **Known bug, just diagnosed, fix given but not yet confirmed as of session end**: after adding the winding fix to the script, the mapshaper regeneration step was re-run against the **stale, still-incorrectly-wound** output file, because the instruction to re-run `prepare_boundaries.py --write` itself was mistakenly omitted in an earlier turn. Every rendered path was showing an identical 800×800 bounding box (the classic "inside-out polygon" signature). **Fix**: re-run `prepare_boundaries.py --write`, then both mapshaper commands, per §7 below. **This was not yet confirmed working as of session end — confirm this first in the new conversation.**
4. **`MapView.jsx` no longer uses `react-simple-maps`' declarative components** (`ComposableMap`/`Geographies`/`Geography`). That library's `projection` prop does not correctly accept a custom factory function in the installed version (`TypeError: projectionStream is not a function` when attempting `projection={(w,h) => geoMercator().fitSize(...)}`) — after multiple failed attempts, the component was rewritten to use `d3-geo`'s `geoMercator`/`geoPath` directly, rendering a plain `<svg>` with one `<path>` per feature. This is simpler and has no library-specific API ambiguity. **`react-simple-maps` remains installed as a dependency** (originally intended for Prompt 4's pan/zoom via `ZoomableGroup`) but is not currently imported anywhere. Current full content of `MapView.jsx` is in Appendix B.

**Immediate next step**: confirm the map renders correctly after the fix in §7, then commit, then continue with Prompt 2.

---

## 7. Exact commands to run first in the new session

```powershell
Set-Location "C:\Users\Lenovo\Desktop\Census Analytics Platform"
git status
git log --oneline
```

Then, if the map still isn't rendering correctly (confirm first with a screenshot at `/tab1`, not the bare root):

```powershell
.\Backend\.venv\Scripts\python.exe Backend\scripts\prepare_boundaries.py --write
```
```powershell
mapshaper "Backend\scripts\_boundary_work\india_states_2011.geojson" -simplify 10% -o "Frontend\src\assets\india-simplified.json" format=geojson
```
```powershell
mapshaper "Backend\scripts\_boundary_work\india_states_2011.geojson" -o "Frontend\src\assets\india-full-detail.json" format=geojson
```

Reload the dev server page and screenshot `/tab1`. Once confirmed working, commit:
```powershell
git add Backend/scripts/prepare_boundaries.py Frontend/src/assets/india-simplified.json Frontend/src/assets/india-full-detail.json Frontend/src/components/MapView.jsx
git commit -m "Fix boundary polygon winding order; switch MapView to direct d3-geo rendering"
```

---

## 8. `PHASE4_PROMPT_SEQUENCE.md` needs two adjustments

Because `MapView.jsx` no longer uses `react-simple-maps`' components:
- **Prompt 2 (metric selector/coloring)**: still valid in spirit (add a metric selector, recolor via `d3-scale` quantile scale), but should target the raw-SVG `<path>` elements' `fill` attribute directly, not react-simple-maps' `<Geography>` styling props.
- **Prompt 4 (pan/zoom)**: originally planned around `react-simple-maps`' `ZoomableGroup`, which "comes free with the library." Since rendering is now raw SVG, this needs to either (a) reintroduce `react-simple-maps` *just* for a `ZoomableGroup` wrapper (if compatible), or (b) implement pan/zoom directly with `d3-zoom`, a stable library with no similar API ambiguity encountered so far. **Decide this when Prompt 4 is actually reached** — not blocking now.

Prompts 3, 5, 6 (labels, click-through, islands inset) are unaffected by the rendering approach change.

---

## 9. Suggested opening prompt for the new conversation

```
Continuing the Census Analytics Platform project. I'm attaching the full
spec set (AGENTS.md, ARCHITECTURE.md, DATABASE.md, API.md, DESIGN.md,
SKILLS.md, ROADMAP.md, tab1_national_map_explorer_spec.md,
tab2_state_comparison_engine_spec.md, RUNBOOK.md,
PHASE4_PROMPT_SEQUENCE.md) plus SESSION_HANDOFF.md, which covers exactly
where the last session left off, including a diagnosed-but-unconfirmed
fix for the current blocking bug. Read SESSION_HANDOFF.md first, then
help me confirm the fix in its §7 and continue from there. Codex is
still out of usage, so I'm executing everything manually — give me exact,
single-line, copy-paste-ready commands as before, one step at a time.
```

---

## Appendix A — current `Backend/scripts/prepare_boundaries.py`

This is the version including the winding fix (`fix_winding()` using `shapely.geometry.polygon.orient()`), the numeric census-code mapping (`CENSUS_CODE_TO_NAME`), and the dry-run centroid safety check. If the file in the repo differs from this, trust the repo version and flag the discrepancy in the new conversation.

```python
"""
Downloads 2011 Census district boundaries (correct vintage — matches
india-districts-census-2011.csv exactly, per DATABASE.md §2) and dissolves
them into 2011-era state/UT boundaries: undivided Andhra Pradesh, undivided
Jammu & Kashmir, Dadra & Nagar Haveli and Daman & Diu still separate.

Source: yashveeeeeeer/india-geodata, "Census 2011 Boundaries and Data"
(CC0-1.0 / CC-BY-NC-SA-4.0, sourced from Registrar General of India + SHRUG).

Run from Backend/: python scripts/prepare_boundaries.py
Requires: pip install py7zr shapely --break-system-packages  (no GDAL/geopandas needed)

IMPORTANT: this script runs in two passes, on purpose.
  1) DRY RUN (default): prints the proposed name for each region plus its
     centroid coordinates, but writes nothing. Check the printed centroids
     against rough known locations before trusting the mapping.
  2) WRITE: only after the dry run looks correct, re-run with --write to
     actually produce the output GeoJSON.
This exists because the source data's state field turned out to be numeric
Census 2011 state codes, not names — a silent wrong mapping here would
mislabel a region everywhere downstream (map, choropleth, API), so this is
not a step to skip or automate past without a human check.

ALSO IMPORTANT: whenever this script is edited, re-run it with --write
again before regenerating anything downstream (e.g. mapshaper). A past
session mistake was re-running mapshaper against a stale output file
after this script was updated but not re-run — don't repeat that.
"""
import argparse
import json
import urllib.request
from pathlib import Path

import py7zr
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from shapely.geometry.polygon import orient

URL = "https://github.com/yashveeeeeeer/india-geodata/releases/download/census/2011/Districts_2011.geojsonl.7z"
WORKDIR = Path(__file__).parent / "_boundary_work"
WORKDIR.mkdir(exist_ok=True)
ARCHIVE = WORKDIR / "Districts_2011.geojsonl.7z"
OUTPUT_STATE_LEVEL = WORKDIR / "india_states_2011.geojson"

STATE_FIELD_CANDIDATES = ["ST_NM", "STATE", "State_Name", "st_nm", "STNAME", "NAME_1"]

CENSUS_CODE_TO_NAME = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab",
    "04": "Chandigarh", "05": "Uttarakhand", "06": "Haryana",
    "07": "NCT of Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "25": "Daman and Diu", "26": "Dadra and Nagar Haveli",
    "27": "Maharashtra", "28": "Andhra Pradesh", "29": "Karnataka",
    "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar Islands",
}

EXPECTED_ROUGH_LOCATION = {
    "Jammu and Kashmir": (34, 76), "Himachal Pradesh": (32, 77),
    "Punjab": (31, 75), "Chandigarh": (30.7, 76.8), "Uttarakhand": (30, 79),
    "Haryana": (29, 76), "NCT of Delhi": (28.6, 77.2), "Rajasthan": (27, 74),
    "Uttar Pradesh": (27, 80), "Bihar": (25.5, 85.5), "Sikkim": (27.5, 88.5),
    "Arunachal Pradesh": (28, 94.5), "Nagaland": (26, 94.5),
    "Manipur": (24.7, 93.9), "Mizoram": (23.3, 92.7), "Tripura": (23.8, 91.5),
    "Meghalaya": (25.5, 91), "Assam": (26.5, 92.8), "West Bengal": (23.5, 87.5),
    "Jharkhand": (23.6, 85.3), "Odisha": (20.5, 84.5), "Chhattisgarh": (21.5, 82),
    "Madhya Pradesh": (23, 78), "Gujarat": (22.5, 71.5),
    "Daman and Diu": (20.5, 71.5), "Dadra and Nagar Haveli": (20.2, 73),
    "Maharashtra": (19.5, 76), "Andhra Pradesh": (16, 80),
    "Karnataka": (15, 76), "Goa": (15.4, 74), "Lakshadweep": (10.5, 72.6),
    "Kerala": (10.5, 76.3), "Tamil Nadu": (11, 78.5), "Puducherry": (11.9, 79.8),
    "Andaman and Nicobar Islands": (11, 92.8),
}


def download():
    if ARCHIVE.exists():
        print(f"Already downloaded: {ARCHIVE}")
        return
    print(f"Downloading {URL} ...")
    urllib.request.urlretrieve(URL, ARCHIVE)
    print(f"Saved to {ARCHIVE} ({ARCHIVE.stat().st_size / 1e6:.1f} MB)")


def extract():
    geojsonl_files = list(WORKDIR.glob("*.geojsonl")) + list(WORKDIR.glob("*.jsonl"))
    if geojsonl_files:
        return geojsonl_files[0]
    with py7zr.SevenZipFile(ARCHIVE, mode="r") as z:
        z.extractall(path=WORKDIR)
    geojsonl_files = list(WORKDIR.glob("*.geojsonl")) + list(WORKDIR.glob("*.jsonl"))
    if not geojsonl_files:
        raise SystemExit(
            f"No .geojsonl file found after extraction. Contents: {list(WORKDIR.iterdir())}"
        )
    return geojsonl_files[0]


def detect_state_field(sample_feature: dict) -> str:
    props = sample_feature.get("properties", {})
    for candidate in STATE_FIELD_CANDIDATES:
        if candidate in props:
            return candidate
    raise SystemExit(
        "Could not auto-detect the state name field. "
        f"Available properties on first feature: {list(props.keys())}\n"
        "Add the correct field name to STATE_FIELD_CANDIDATES and re-run."
    )


def load_features(geojsonl_path: Path):
    features = []
    with open(geojsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                features.append(json.loads(line))
    return features


def resolve_name(raw_value: str) -> str:
    raw = raw_value.strip()
    if raw in CENSUS_CODE_TO_NAME:
        return CENSUS_CODE_TO_NAME[raw]
    legacy = {"ORISSA": "Odisha", "PONDICHERRY": "Puducherry", "NCT OF DELHI": "NCT of Delhi"}
    return legacy.get(raw.upper(), raw)


def group_and_dissolve(features: list[dict]):
    state_field = detect_state_field(features[0])
    print(f"Using state field: {state_field}\n")

    by_state: dict[str, list] = {}
    for feat in features:
        raw = str(feat["properties"][state_field])
        name = resolve_name(raw)
        by_state.setdefault(name, []).append(shape(feat["geometry"]))

    if len(by_state) != 35:
        print(
            f"WARNING: expected 35 states/UTs, got {len(by_state)}. "
            "Stop and investigate before proceeding either way."
        )

    dissolved = {}
    for name, geoms in sorted(by_state.items()):
        dissolved[name] = unary_union(geoms)
    return dissolved


def dry_run_report(dissolved: dict):
    print(f"{'Name':32s} {'Centroid (lat, lon)':>22s}  Check")
    print("-" * 90)
    any_flag = False
    for name, geom in dissolved.items():
        c = geom.centroid
        actual = (round(c.y, 1), round(c.x, 1))
        expected = EXPECTED_ROUGH_LOCATION.get(name)
        flag = ""
        if expected is None:
            flag = "NO EXPECTED VALUE ON FILE"
            any_flag = True
        elif abs(actual[0] - expected[0]) > 4 or abs(actual[1] - expected[1]) > 4:
            flag = "!! FAR FROM EXPECTED — CHECK THIS ONE"
            any_flag = True
        print(f"{name:32s} {str(actual):>22s}  {flag}")
    print("-" * 90)
    if any_flag:
        print(
            "\nAt least one region is flagged above. Do NOT proceed to --write "
            "until every flagged row has been manually checked and resolved."
        )
    else:
        print(
            "\nAll centroids look roughly consistent with expected locations. "
            "If this matches your own visual expectation of India's geography, "
            "re-run with --write to produce the output file."
        )


def fix_winding(geom):
    """
    Shapely's unary_union() follows the traditional GIS/OGC winding
    convention (clockwise exterior rings). GeoJSON (RFC 7946), and by
    extension d3-geo/react-simple-maps, require the opposite: exterior
    rings counter-clockwise, holes clockwise. Without this fix, D3 treats
    each polygon as inside-out and renders it filling nearly the whole
    canvas — this was the actual cause of the "tiny shape" / "blank map" /
    "every path is 800x800" symptoms across this whole debugging session.
    """
    if geom.geom_type == "Polygon":
        return orient(geom, sign=1.0)
    if geom.geom_type == "MultiPolygon":
        from shapely.geometry import MultiPolygon
        return MultiPolygon([orient(p, sign=1.0) for p in geom.geoms])
    return geom


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Actually write the output file (default: dry run only)")
    args = parser.parse_args()

    download()
    geojsonl_path = extract()
    print(f"Extracted: {geojsonl_path}")
    features = load_features(geojsonl_path)
    print(f"Loaded {len(features)} district features\n")

    dissolved = group_and_dissolve(features)
    dissolved = {name: fix_winding(geom) for name, geom in dissolved.items()}

    if not args.write:
        dry_run_report(dissolved)
        return

    state_geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"name": name}, "geometry": mapping(geom)}
            for name, geom in dissolved.items()
        ],
    }
    with open(OUTPUT_STATE_LEVEL, "w", encoding="utf-8") as f:
        json.dump(state_geojson, f)
    print(f"Wrote state-level 2011 boundaries to: {OUTPUT_STATE_LEVEL}")


if __name__ == "__main__":
    main()
```

---

## Appendix B — current `Frontend/src/components/MapView.jsx`

```jsx
import { geoMercator, geoPath } from "d3-geo";
import indiaGeoJson from "../assets/india-simplified.json";

const WIDTH = 900;
const HEIGHT = 800;

// Computed once, at module load — fitSize gives the correct scale and
// translate for this exact geometry and canvas size, no guessing.
const projection = geoMercator().fitSize([WIDTH, HEIGHT], indiaGeoJson);
const pathGenerator = geoPath(projection);

export function MapView() {
  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      {indiaGeoJson.features.map((feature) => (
        <path
          key={feature.properties.name}
          d={pathGenerator(feature)}
          stroke="#334155"
          strokeWidth={0.5}
          fill="#e2e8f0"
        />
      ))}
    </svg>
  );
}

export default MapView;
```
