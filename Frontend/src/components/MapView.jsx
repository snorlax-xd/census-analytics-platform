import { geoMercator, geoPath } from "d3-geo";
import indiaGeoJson from "../assets/india-simplified.json";
import { localeCodeByName } from "../lib/locales";

const WIDTH = 900;
const HEIGHT = 800;
const EXPECTED_FEATURE_COUNT = 35; // 2011-era states/UTs — see DATABASE.md §2

// Computed once, at module load — fitSize gives the correct scale and
// translate for this exact geometry and canvas size, no guessing.
const projection = geoMercator().fitSize([WIDTH, HEIGHT], indiaGeoJson);
const pathGenerator = geoPath(projection);

/**
 * Validates the loaded boundary data BEFORE rendering, instead of trusting
 * a well-formed-JSON import to also mean well-formed-geometry.
 *
 * This exists because of a real bug: a ring-winding regression in the
 * boundary generation pipeline produced perfectly valid JSON where every
 * single feature's projected bounding box collapsed to the exact canvas
 * edges (d3-geo treating each polygon as inside-out). The app rendered a
 * silent blank <svg> with no error — nothing distinguished "no data" from
 * "wrong data" from "correct but empty" at a glance, and diagnosing it took
 * a full manual investigation. This check catches that exact signature
 * automatically, so a future regeneration bug fails immediately and
 * specifically instead of reappearing as an unexplained blank map.
 *
 * If this throws, the fix is almost always: re-run rebuild_boundaries.ps1
 * (see SESSION_HANDOFF.md for why mapshaper alone isn't enough).
 */
function validateBoundaryData(geojson) {
  const features = geojson?.features;

  if (!Array.isArray(features) || features.length === 0) {
    throw new Error(
      "Boundary data has no features. india-simplified.json is empty or malformed — " +
        "re-run rebuild_boundaries.ps1."
    );
  }

  if (features.length !== EXPECTED_FEATURE_COUNT) {
    throw new Error(
      `Boundary data has ${features.length} features, expected ${EXPECTED_FEATURE_COUNT} ` +
        "(2011-era states/UTs). Re-run rebuild_boundaries.ps1 and check prepare_boundaries.py's " +
        "dry-run report for a state-count mismatch."
    );
  }

  // The specific signature of the winding-order bug: every feature's
  // projected bounds collapsing to the exact canvas frame.
  const boundsList = features.map((f) => pathGenerator.bounds(f));
  const allIdentical = boundsList.every(
    (b) =>
      b[0][0] === boundsList[0][0][0] &&
      b[0][1] === boundsList[0][0][1] &&
      b[1][0] === boundsList[0][1][0] &&
      b[1][1] === boundsList[0][1][1]
  );

  if (allIdentical) {
    const [[x0, y0], [x1, y1]] = boundsList[0];
    throw new Error(
      `All ${features.length} features share an identical projected bounding box ` +
        `([${x0.toFixed(0)},${y0.toFixed(0)}] to [${x1.toFixed(0)},${y1.toFixed(0)}]), ` +
        "matching the canvas frame. This is the ring-winding regression signature " +
        "(mapshaper normalizes winding on export — see fix_winding_post_mapshaper.py). " +
        "Re-run rebuild_boundaries.ps1, specifically confirm step 4/4 ran."
    );
  }

  return true;
}

let validationError = null;
try {
  validateBoundaryData(indiaGeoJson);
} catch (err) {
  validationError = err;
  // Surface it in the console immediately too, not just in the UI, so it
  // shows up even if the error UI is missed on a quick glance.
  console.error("[MapView] Boundary data validation failed:", err.message);
}

export function MapView({ valuesByCode = new Map(), colorForValue = (_value) => "#e2e8f0" }) {
  if (validationError) {
    return (
      <div
        role="alert"
        style={{
          padding: "1.5rem",
          border: "1px solid #dc2626",
          borderRadius: "0.5rem",
          background: "#fef2f2",
          color: "#991b1b",
          fontFamily: "monospace",
          fontSize: "0.875rem",
          whiteSpace: "pre-wrap",
        }}
      >
        <strong>MapView failed to load boundary data:</strong>
        {"\n\n"}
        {validationError.message}
      </div>
    );
  }

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      {indiaGeoJson.features.map((feature) => (
        <g key={feature.properties.name}>
          <path
            d={pathGenerator(feature)}
            stroke="#f8fafc"
            strokeWidth={0.8}
            fill={colorForValue(valuesByCode.get(localeCodeByName.get(feature.properties.name)))}
          />
          {localeCodeByName.has(feature.properties.name) ? (
            <text
              x={pathGenerator.centroid(feature)[0]}
              y={pathGenerator.centroid(feature)[1]}
              textAnchor="middle"
              dominantBaseline="central"
              fill="#0f172a"
              fontSize={11}
              fontWeight={700}
              pointerEvents="none"
              paintOrder="stroke"
              stroke="#ffffff"
              strokeWidth={2.5}
            >
              {localeCodeByName.get(feature.properties.name)}
            </text>
          ) : null}
        </g>
      ))}
    </svg>
  );
}

export default MapView;
