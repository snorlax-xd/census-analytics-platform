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
"""
import argparse
import json
import urllib.request
from pathlib import Path

import py7zr
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

URL = "https://github.com/yashveeeeeeer/india-geodata/releases/download/census/2011/Districts_2011.geojsonl.7z"
WORKDIR = Path(__file__).parent / "_boundary_work"
WORKDIR.mkdir(exist_ok=True)
ARCHIVE = WORKDIR / "Districts_2011.geojsonl.7z"
OUTPUT_STATE_LEVEL = WORKDIR / "india_states_2011.geojson"

STATE_FIELD_CANDIDATES = ["ST_NM", "STATE", "State_Name", "st_nm", "STNAME", "NAME_1"]

# Standard Census of India 2011 state/UT census codes. This is a well-known
# government convention, but is still being verified via the dry-run
# centroid check below rather than trusted outright — see module docstring.
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

# Rough expected centroid (lat, lon) for a sanity check — not precise,
# just enough to catch a gross mislabel (e.g. a tiny island territory
# centroid landing in the middle of the mainland would be a red flag).
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
    """Map either a numeric census code or an already-textual name to our
    standard state/UT name."""
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