# Backend/scripts/diagnose_mapshaper_output.py
import json
from shapely.geometry import shape

path = r"Frontend\src\assets\india-simplified.json"
data = json.load(open(path, encoding="utf-8"))

print(f"Type: {data.get('type')}")
print(f"Feature count: {len(data['features'])}")
print(f"Top-level keys: {list(data.keys())}\n")

print(f"{'Name':32s} {'minLon':>8s} {'maxLon':>8s} {'minLat':>8s} {'maxLat':>8s} {'valid':>6s} {'geomtype':>12s}")
print("-" * 100)
for feat in data["features"][:8]:
    name = feat["properties"].get("name", "?")
    gtype = feat["geometry"]["type"]
    geom = shape(feat["geometry"])
    minx, miny, maxx, maxy = geom.bounds
    print(f"{name:32s} {minx:8.2f} {maxx:8.2f} {miny:8.2f} {maxy:8.2f} {str(geom.is_valid):>6s} {gtype:>12s}")