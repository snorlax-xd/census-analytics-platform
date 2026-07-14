import { useMemo, useState } from "react";

import { MapView } from "../components/MapView";
import { useAnalyticsQuery } from "../api/queries";
import { createChoroplethScale } from "../lib/colorScale";
import { localeCodes } from "../lib/locales";

const metricOptions = [
  { code: "population", label: "Population" },
  { code: "sex_ratio", label: "Sex Ratio" },
  { code: "literacy_rate", label: "Literacy Rate" },
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
  const [selectedMetric, setSelectedMetric] = useState(metricOptions[0].code);
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

        <div className="inline-flex w-fit rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
          {metricOptions.map((metric) => (
            <button
              key={metric.code}
              type="button"
              onClick={() => setSelectedMetric(metric.code)}
              className={`rounded-md px-4 py-2 text-sm font-semibold transition ${
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

          <div className="flex flex-wrap items-center gap-3">
            {analyticsQuery.isLoading ? (
              <span className="text-sm text-slate-500">Loading metric data...</span>
            ) : analyticsQuery.isError ? (
              <span className="text-sm font-medium text-red-600">
                Could not load metric data.
              </span>
            ) : (
              metricValues.buckets.map((bucket) => (
                <div key={`${bucket.color}-${bucket.min}-${bucket.max}`} className="flex items-center gap-2">
                  <span
                    className="h-3 w-5 rounded-sm border border-slate-200"
                    style={{ backgroundColor: bucket.color }}
                  />
                  <span className="text-xs font-medium text-slate-600">
                    {formatValue(bucket.min, metricValues.unit)} -{" "}
                    {formatValue(bucket.max, metricValues.unit)}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        <MapView
          valuesByCode={metricValues.valuesByCode}
          colorForValue={metricValues.colorForValue}
        />
      </div>
    </section>
  );
}
