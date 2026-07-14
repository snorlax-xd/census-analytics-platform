"""
Run this AFTER every mapshaper command that touches the India boundary
files. mapshaper's GeoJSON writer normalizes ring winding to RFC7946
(counter-clockwise exterior) on export, unconditionally, regardless of
what winding it was given as input and regardless of the `rfc7946` CLI
flag (that flag controls antimeridian handling, not this). Confirmed by
direct test: sign=1.0 and sign=-1.0 both produced identical, still-broken
output after being piped through mapshaper, while sign=-1.0 applied with
NO mapshaper step in between rendered correctly through d3-geo.

So: mapshaper is left in the pipeline (still needed for -simplify), and
this script re-applies the CW-exterior fix as the final step, directly
on the files mapshaper wrote, right before the frontend loads them.

Usage: python scripts/fix_winding_post_mapshaper.py
Operates in place on both:
  Frontend/src/assets/india-simplified.json
  Frontend/src/assets/india-full-detail.json
"""
import json
from pathlib import Path

from shapely.geometry import shape, mapping, MultiPolygon
from shapely.geometry.polygon import orient

REPO_ROOT = Path(__file__).parent.parent.parent  # Backend/scripts -> repo root
TARGETS = [
    REPO_ROOT / "Frontend" / "src" / "assets" / "india-simplified.json",
    REPO_ROOT / "Frontend" / "src" / "assets" / "india-full-detail.json",
]


def fix_winding(geom):
    if geom.geom_type == "Polygon":
        return orient(geom, sign=-1.0)
    if geom.geom_type == "MultiPolygon":
        return MultiPolygon([orient(p, sign=-1.0) for p in geom.geoms])
    return geom


def process(path: Path):
    if not path.exists():
        print(f"SKIP (not found): {path}")
        return

    data = json.loads(path.read_text(encoding="utf-8"))
    fixed_count = 0
    still_ccw = []

    for feat in data["features"]:
        geom = shape(feat["geometry"])
        # is_ccw check on the exterior ring, before fixing, just for the report
        ring = geom.exterior if geom.geom_type == "Polygon" else geom.geoms[0].exterior
        was_ccw = ring.is_ccw
        geom = fix_winding(geom)
        feat["geometry"] = mapping(geom)
        fixed_count += 1
        if was_ccw:
            still_ccw.append(feat["properties"].get("name", "?"))

    path.write_text(json.dumps(data), encoding="utf-8")
    print(f"Fixed {fixed_count} features in {path}")
    print(f"  (mapshaper had left {len(still_ccw)} of them CCW before this fix ran)")


def main():
    for path in TARGETS:
        process(path)


if __name__ == "__main__":
    main()