# Backend/scripts/diagnose_boundaries.py
import json
from shapely.geometry import shape

INDIA_LON = (68, 98)
INDIA_LAT = (6, 38)

path = r"Backend\scripts\_boundary_work\india_states_2011.geojson"
data = json.load(open(path, encoding="utf-8"))

print(f"{'Name':32s} {'minLon':>8s} {'maxLon':>8s} {'minLat':>8s} {'maxLat':>8s} {'valid':>6s}  flag")
print("-" * 100)
for feat in data["features"]:
    name = feat["properties"].get("name", "?")
    geom = shape(feat["geometry"])
    minx, miny, maxx, maxy = geom.bounds
    flag = ""
    if minx < INDIA_LON[0] - 2 or maxx > INDIA_LON[1] + 2:
        flag += " LON OUT OF RANGE"
    if miny < INDIA_LAT[0] - 2 or maxy > INDIA_LAT[1] + 2:
        flag += " LAT OUT OF RANGE"
    if not geom.is_valid:
        flag += " INVALID GEOMETRY"
    print(f"{name:32s} {minx:8.2f} {maxx:8.2f} {miny:8.2f} {maxy:8.2f} {str(geom.is_valid):>6s}  {flag}")
    