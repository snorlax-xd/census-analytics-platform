import { useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";

import { MapView } from "../components/MapView";
import { useAnalyticsQuery } from "../api/queries";
import { createChoroplethScale } from "../lib/colorScale";
import { localeCodes } from "../lib/locales";

const metricOptions = [
  { code: "population", label: "Population" },
  { code: "sex_ratio", label: "Sex Ratio" },
  { code: "literacy_rate", label: "Literacy Rate" },
];

const metricCodes = new Set(metricOptions.map((metric) => metric.code));

const zoomTargets = [
  { label: "Northeast", center: [94, 26], zoom: 3.2 },
  { label: "Delhi NCR", center: [77.2, 28.6], zoom: 5.2 },
];

const numberFormatter = new Intl.NumberFormat("en-IN", {
  maximumFractionDigits: 1,
});

function formatValue(value: number, unit?: string) {
  const formatted = numberFormatter.format(value);

  if (unit === "%") {
    return `${formatted}%`;
  }

  return formatted;
}

export function Tab1() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const metricFromUrl = searchParams.get("metric");
  const initialMetric = metricFromUrl && metricCodes.has(metricFromUrl) ? metricFromUrl : metricOptions[0].code;
  const [selectedMetric, setSelectedMetric] = useState(initialMetric);
  const [mapPosition, setMapPosition] = useState({ center: [82, 22], zoom: 1 });
  const analyticsQuery = useAnalyticsQuery(localeCodes);

  const metricValues = useMemo(() => {
    const valuesByCode = new Map<string, number>();
    let unit = "";

    for (const locale of analyticsQuery.data?.data ?? []) {
      const measure = locale.measures.find((item) => item.measure_code === selectedMetric);

      if (measure) {
        valuesByCode.set(locale.locale_code, measure.value);
        unit = measure.unit;
      }
    }

    const scale = createChoroplethScale([...valuesByCode.values()]);

    return {
      valuesByCode,
      unit,
      ...scale,
    };
  }, [analyticsQuery.data, selectedMetric]);

  const selectedMetricLabel =
    metricOptions.find((metric) => metric.code === selectedMetric)?.label ?? "Metric";

  function selectMetric(metricCode: string) {
    setSelectedMetric(metricCode);
    setSearchParams({ metric: metricCode }, { replace: true });
  }

  function focusRegion(center: number[], zoom: number) {
    setMapPosition({ center, zoom });
  }

  function openState(code: string) {
    navigate(`/tab1/state/${code}?metric=${selectedMetric}`);
  }

  return (
    <section className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Tab 1</p>
          <h2 className="text-2xl font-semibold text-slate-950">National Map Explorer</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">
            Data as of Census 2011, using 2011-era state and Union Territory boundaries.
          </p>
        </div>

        <div className="inline-flex w-fit rounded-xl border border-slate-300 bg-white p-ui-1 shadow-card">
          {metricOptions.map((metric) => (
            <button
              key={metric.code}
              type="button"
              onClick={() => selectMetric(metric.code)}
              className={`rounded-lg px-ui-4 py-ui-2 text-ui-body font-ui-semibold transition ${
                selectedMetric === metric.code
                  ? "bg-slate-950 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {metric.label}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              {selectedMetricLabel}
            </p>
            <h3 className="text-lg font-semibold text-slate-950">India, Census 2011</h3>
          </div>

          <div className="flex flex-wrap items-center gap-x-ui-4 gap-y-ui-2">
            {analyticsQuery.isLoading ? (
              <span className="text-sm text-slate-500">Loading metric data...</span>
            ) : analyticsQuery.isError ? (
              <span className="text-sm font-medium text-red-600">
                Could not load metric data.
              </span>
            ) : (
              metricValues.buckets.map((bucket) => (
                <div
                  key={`${bucket.color}-${bucket.min}-${bucket.max}`}
                  className="flex items-center gap-ui-2 rounded-md border border-slate-200 bg-white/80 px-ui-2 py-ui-1 shadow-card"
                >
                  <span
                    className="h-ui-2 w-ui-5 rounded-sm border border-slate-200"
                    style={{ backgroundColor: bucket.color }}
                  />
                  <span className="text-ui-caption font-ui-semibold text-slate-600">
                    {formatValue(bucket.min, metricValues.unit)} -{" "}
                    {formatValue(bucket.max, metricValues.unit)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="border-b border-slate-200 px-5 py-3">
          <div className="flex flex-wrap items-center gap-ui-2">
            {zoomTargets.map((target) => (
              <button
                key={target.label}
                type="button"
                onClick={() => focusRegion(target.center, target.zoom)}
                className="rounded-full border border-teal-200 bg-teal-50 px-ui-3 py-ui-1 text-ui-caption font-ui-semibold text-teal-800 shadow-card transition hover:bg-teal-100"
              >
                {target.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-0 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="min-w-0">
            <MapView
              valuesByCode={metricValues.valuesByCode}
              colorForValue={metricValues.colorForValue}
              zoomEnabled
              zoomCenter={mapPosition.center}
              zoom={mapPosition.zoom}
              avoidLabelCollisions
              onMoveEnd={({ coordinates, zoom }: { coordinates: number[]; zoom: number }) =>
                setMapPosition({ center: coordinates, zoom })
              }
              onStateClick={openState}
            />
          </div>

          <div className="border-t border-slate-200 bg-slate-50/80 p-4 lg:border-l lg:border-t-0">
            <div className="sticky top-4 rounded-md border border-slate-200 bg-white p-4 shadow-sm">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Islands
              </p>
              <MapView
                valuesByCode={metricValues.valuesByCode}
                colorForValue={metricValues.colorForValue}
                featureCodes={["AN", "LD"]}
                showLabels
                islandInset
                avoidLabelCollisions={false}
                onStateClick={openState}
              />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
