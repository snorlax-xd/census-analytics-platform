import { useMemo } from "react";
import { geoMercator, geoPath } from "d3-geo";
import { ComposableMap, ZoomableGroup } from "react-simple-maps";
import indiaIslandsGeoJson from "../assets/india-islands-detail.json";
import indiaGeoJson from "../assets/india-simplified.json";
import { localeCodeByName } from "../lib/locales";

const WIDTH = 900;
const HEIGHT = 800;
const ISLAND_LAYOUTS = new Map([
  ["AN", { x: 40, y: 52, width: 820, height: 310, label: "Andaman & Nicobar" }],
  ["LD", { x: 40, y: 450, width: 820, height: 290, label: "Lakshadweep" }],
]);
const EXPECTED_FEATURE_COUNT = 35; // 2011-era states/UTs — see DATABASE.md §2

// Computed once, at module load — fitSize gives the correct scale and
// translate for this exact geometry and canvas size, no guessing.
const defaultProjection = geoMercator().fitSize([WIDTH, HEIGHT], indiaGeoJson);
const defaultPathGenerator = geoPath(defaultProjection);

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
  const boundsList = features.map((f) => defaultPathGenerator.bounds(f));
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

/**
 * @param {{
 *   valuesByCode?: Map<string, number>,
 *   colorForValue?: (value: number | undefined) => string,
 *   featureCodes?: string[],
 *   zoomEnabled?: boolean,
 *   zoomCenter?: number[],
 *   zoom?: number,
 *   onMoveEnd?: (position: { coordinates: number[], zoom: number }) => void,
 *   onStateClick?: (code: string) => void,
 *   selectedCode?: string,
 *   dimUnselected?: boolean,
 *   showLabels?: boolean,
 *   avoidLabelCollisions?: boolean,
 *   islandInset?: boolean,
 *   className?: string,
 * }} props
 */
export function MapView({
  valuesByCode = new Map(),
  colorForValue = (_value) => "#e2e8f0",
  featureCodes = undefined,
  zoomEnabled = false,
  zoomCenter = [82, 22],
  zoom = 1,
  onMoveEnd = undefined,
  onStateClick = undefined,
  selectedCode = undefined,
  dimUnselected = false,
  showLabels = true,
  avoidLabelCollisions = false,
  islandInset = false,
  className = "",
}) {
  const filteredFeatures = useMemo(() => {
    const wantedCodes = featureCodes ? new Set(featureCodes) : null;
    const sourceGeoJson = islandInset ? indiaIslandsGeoJson : indiaGeoJson;

    return sourceGeoJson.features.filter((feature) => {
      const code = localeCodeByName.get(feature.properties.name);
      return !wantedCodes || wantedCodes.has(code);
    });
  }, [featureCodes, islandInset]);

  const pathGenerator = useMemo(() => {
    if (!featureCodes) {
      return defaultPathGenerator;
    }

    if (islandInset) {
      return null;
    }

    return geoPath(
      geoMercator().fitSize([WIDTH, HEIGHT], {
        type: "FeatureCollection",
        features: filteredFeatures,
      })
    );
  }, [featureCodes, filteredFeatures, islandInset]);

  const islandPathGenerators = useMemo(() => {
    if (!islandInset) {
      return new Map();
    }

    return new Map(
      filteredFeatures.map((feature) => {
        const code = localeCodeByName.get(feature.properties.name);
        const layout = ISLAND_LAYOUTS.get(code) ?? { x: 40, y: 40, width: 820, height: 720 };
        const projection = geoMercator().fitSize([layout.width, layout.height], feature);

        return [code, { layout, path: geoPath(projection) }];
      })
    );
  }, [filteredFeatures, islandInset]);

  const labelFeatures = useMemo(() => {
    if (!showLabels) {
      return new Set();
    }

    if (!avoidLabelCollisions) {
      return new Set(filteredFeatures.map((feature) => localeCodeByName.get(feature.properties.name)));
    }

    const placed = [];
    const visible = new Set();
    const labelScale = zoomEnabled ? Math.max(zoom, 1) : 1;
    const candidates = filteredFeatures
      .map((feature) => {
        const code = localeCodeByName.get(feature.properties.name);
        const islandGenerator = islandPathGenerators.get(code);
        const generator = islandInset ? islandGenerator?.path : pathGenerator;
        const bounds = generator?.bounds(feature);
        const centroid = generator?.centroid(feature);
        const area = bounds
          ? Math.max(1, (bounds[1][0] - bounds[0][0]) * (bounds[1][1] - bounds[0][1]))
          : 1;

        return { feature, code, centroid, area };
      })
      .filter((item) => item.code && item.centroid)
      .sort((left, right) => right.area - left.area);

    for (const item of candidates) {
      const width = (item.code.length * 7 + 8) / labelScale;
      const height = 14 / labelScale;
      const box = {
        left: item.centroid[0] - width / 2,
        right: item.centroid[0] + width / 2,
        top: item.centroid[1] - height / 2,
        bottom: item.centroid[1] + height / 2,
      };
      const collides = placed.some(
        (existing) =>
          box.left < existing.right &&
          box.right > existing.left &&
          box.top < existing.bottom &&
          box.bottom > existing.top
      );

      if (!collides) {
        placed.push(box);
        visible.add(item.code);
      }
    }

    return visible;
  }, [
    avoidLabelCollisions,
    filteredFeatures,
    islandInset,
    islandPathGenerators,
    pathGenerator,
    showLabels,
    zoom,
    zoomEnabled,
  ]);

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

  const mapContent = (
    <>
      {filteredFeatures.map((feature) => {
        const code = localeCodeByName.get(feature.properties.name);
        const isDimmed = dimUnselected && selectedCode && code !== selectedCode;
        const islandGenerator = islandPathGenerators.get(code);
        const generator = islandInset ? islandGenerator?.path : pathGenerator;
        const centroid = generator?.centroid(feature);
        const layout = islandGenerator?.layout;

        return (
        <g
          key={feature.properties.name}
          transform={layout ? `translate(${layout.x} ${layout.y})` : undefined}
        >
          {islandInset && layout ? (
            <text
              x={0}
              y={-18}
              fill="#475569"
              fontSize={28}
              fontWeight={700}
              pointerEvents="none"
            >
              {layout.label}
            </text>
          ) : null}
          <path
            d={generator?.(feature)}
            className={onStateClick && code ? "map-state-clickable" : undefined}
            stroke="#f8fafc"
            strokeWidth={islandInset ? 2.2 : 0.8}
            fill={colorForValue(valuesByCode.get(code))}
            opacity={isDimmed ? 0.16 : 1}
            role={onStateClick && code ? "button" : undefined}
            tabIndex={onStateClick && code ? 0 : undefined}
            style={{ cursor: onStateClick && code ? "pointer" : "default" }}
            onClick={onStateClick && code ? () => onStateClick(code) : undefined}
            onKeyDown={
              onStateClick && code
                ? (event) => {
                    if (event.key === "Enter" || event.key === " ") {
                      event.preventDefault();
                      onStateClick(code);
                    }
                  }
                : undefined
            }
          />
          {showLabels && code && centroid && labelFeatures.has(code) ? (
            <text
              x={centroid[0]}
              y={centroid[1]}
              textAnchor="middle"
              dominantBaseline="central"
              fill="#0f172a"
              fontSize={islandInset ? 34 : 11 / (zoomEnabled ? Math.max(zoom, 1) : 1)}
              fontWeight={700}
              pointerEvents="none"
              paintOrder="stroke"
              stroke="#ffffff"
              strokeWidth={islandInset ? 7 : 2.5 / (zoomEnabled ? Math.max(zoom, 1) : 1)}
            >
              {code}
            </text>
          ) : null}
        </g>
        );
      })}
    </>
  );

  if (zoomEnabled) {
    return (
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ center: [82, 22], scale: 1300 }}
        width={WIDTH}
        height={HEIGHT}
        className={`h-auto w-full ${className}`}
      >
        <ZoomableGroup
          center={zoomCenter}
          zoom={zoom}
          minZoom={1}
          maxZoom={8}
          onMoveEnd={onMoveEnd}
        >
          {mapContent}
        </ZoomableGroup>
      </ComposableMap>
    );
  }

  return (
    <svg
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      className={className}
      style={{ width: "100%", height: "auto", display: "block" }}
    >
      {mapContent}
    </svg>
  );
}

export default MapView;
