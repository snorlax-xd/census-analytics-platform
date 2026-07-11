import { ComposableMap, Geographies, Geography } from "react-simple-maps";

import indiaSimplifiedUrl from "../assets/india-simplified.geojson?url";

export function MapView() {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <ComposableMap
        projection="geoMercator"
        projectionConfig={{ center: [82, 22], scale: 900 }}
        width={900}
        height={820}
        className="h-[72vh] min-h-[560px] w-full"
      >
        <Geographies geography={indiaSimplifiedUrl}>
          {({ geographies }) =>
            geographies.map((geo) => (
              <Geography
                key={geo.rsmKey}
                geography={geo}
                tabIndex={-1}
                style={{
                  default: {
                    fill: "#f8fafc",
                    outline: "none",
                    stroke: "#334155",
                    strokeWidth: 0.75,
                  },
                  hover: {
                    fill: "#f8fafc",
                    outline: "none",
                    stroke: "#334155",
                    strokeWidth: 0.75,
                  },
                  pressed: {
                    fill: "#f8fafc",
                    outline: "none",
                    stroke: "#334155",
                    strokeWidth: 0.75,
                  },
                }}
              />
            ))
          }
        </Geographies>
      </ComposableMap>
    </div>
  );
}
