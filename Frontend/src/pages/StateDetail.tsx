import { useMemo } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import type { AnalyticsResponse, MeasureValue } from "../api/client";
import { useAnalyticsQuery } from "../api/queries";
import { MapView } from "../components/MapView";
import { createChoroplethScale } from "../lib/colorScale";
import { formatCategoryName, formatMeasureName } from "../lib/formatMeasure";
import { localeByCode, localeCodes } from "../lib/locales";

const metricOptions = [
  { code: "population", label: "Population" },
  { code: "sex_ratio", label: "Sex Ratio" },
  { code: "literacy_rate", label: "Literacy Rate" },
];

const metricCodes = new Set(metricOptions.map((metric) => metric.code));

const numberFormatter = new Intl.NumberFormat("en-IN", {
  maximumFractionDigits: 1,
});

function formatValue(value: number, unit: string) {
  const formatted = numberFormatter.format(value);

  if (unit === "%") {
    return `${formatted}%`;
  }

  return formatted;
}

function sortMeasuresByName(left: MeasureValue, right: MeasureValue) {
  return formatMeasureName(left.measure_code, left.measure_name).localeCompare(
    formatMeasureName(right.measure_code, right.measure_name)
  );
}

export function StateDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const stateCode = id?.toUpperCase() ?? "";
  const locale = localeByCode.get(stateCode);
  const metricFromUrl = searchParams.get("metric");
  const selectedMetric =
    metricFromUrl && metricCodes.has(metricFromUrl) ? metricFromUrl : metricOptions[0].code;

  const stateQuery = useAnalyticsQuery(stateCode ? [stateCode] : []);
  const cachedNationalData = queryClient.getQueryData<AnalyticsResponse>([
    "analytics",
    localeCodes,
    2011,
    false,
  ]);

  const backgroundMetricValues = useMemo(() => {
    const valuesByCode = new Map<string, number>();

    for (const localeAnalytics of cachedNationalData?.data ?? []) {
      const measure = localeAnalytics.measures.find(
        (item) => item.measure_code === selectedMetric
      );

      if (measure) {
        valuesByCode.set(localeAnalytics.locale_code, measure.value);
      }
    }

    const scale = createChoroplethScale([...valuesByCode.values()]);

    return {
      valuesByCode,
      colorForValue: scale.colorForValue,
    };
  }, [cachedNationalData, selectedMetric]);

  const groupedMeasures = useMemo(() => {
    const measures = stateQuery.data?.data[0]?.measures ?? [];
    const activeMeasure =
      measures.find((measure) => measure.measure_code === selectedMetric) ?? null;
    const groups = new Map<string, MeasureValue[]>();

    for (const measure of measures) {
      if (measure.measure_code === activeMeasure?.measure_code) {
        continue;
      }

      const categoryMeasures = groups.get(measure.category) ?? [];
      categoryMeasures.push(measure);
      groups.set(measure.category, categoryMeasures);
    }

    return {
      activeMeasure,
      categoryGroups: [...groups.entries()]
        .map(([category, categoryMeasures]) => ({
          category,
          measures: categoryMeasures.sort(sortMeasuresByName),
        }))
        .sort((left, right) =>
          formatCategoryName(left.category).localeCompare(formatCategoryName(right.category))
        ),
    };
  }, [selectedMetric, stateQuery.data]);

  function renderMeasureCard(measure: MeasureValue, emphasized = false) {
    return (
      <div
        key={measure.measure_code}
        className={`rounded-md border p-ui-3 ${
          emphasized
            ? "border-teal-600 bg-teal-50 shadow-card"
            : "border-slate-200 bg-white shadow-card"
        }`}
      >
        <p className="text-ui-caption font-ui-semibold text-slate-500">
          {formatMeasureName(measure.measure_code, measure.measure_name)}
        </p>
        <p
          className={`mt-ui-1 font-ui-semibold ${
            emphasized ? "text-ui-display text-teal-700" : "text-ui-title text-slate-950"
          }`}
        >
          {formatValue(measure.value, measure.unit)}
        </p>
        <p className="mt-ui-1 text-ui-caption font-ui-regular text-slate-500">
          {formatCategoryName(measure.category)}
        </p>
      </div>
    );
  }

  if (!locale) {
    return (
      <section className="mx-auto max-w-6xl px-6 py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-5 text-red-700">
          Unknown state code: {stateCode || "missing"}
        </div>
      </section>
    );
  }

  return (
    <section className="relative min-h-[calc(100vh-4rem)] overflow-hidden bg-slate-100 px-6 py-8">
      <div className="pointer-events-none absolute inset-0 z-0 flex items-center justify-center opacity-30 blur-[1.5px]">
        <MapView
          valuesByCode={backgroundMetricValues.valuesByCode}
          colorForValue={backgroundMetricValues.colorForValue}
          selectedCode={stateCode}
          dimUnselected
          showLabels={false}
          className="min-h-full w-full scale-125"
        />
      </div>

      <div className="relative z-10 mx-auto max-w-7xl">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div className="rounded-full border border-slate-200 bg-white/90 px-4 py-2 text-sm font-semibold text-slate-700 shadow-sm">
            National Map / {locale.name}
          </div>

          <button
            type="button"
            onClick={() => navigate(`/tab1?metric=${selectedMetric}`)}
            className="rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-800"
          >
            Minimize
          </button>
        </div>

        <div className="relative min-h-[760px] overflow-hidden rounded-xl border border-slate-200 bg-white/72 shadow-2xl backdrop-blur-sm">
          <div className="absolute inset-0 bg-gradient-to-r from-white/90 via-white/58 to-white/92" />

          <div className="relative z-10 p-6 lg:pr-[390px]">
            <div className="mb-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Focused State View
              </p>
              <h2 className="text-3xl font-semibold text-slate-950">{locale.name}</h2>
              <p className="mt-1 text-sm text-slate-600">Data as of Census 2011</p>
            </div>

            <div className="mx-auto max-w-4xl rounded-lg border border-slate-200 bg-white/80 p-5 shadow-xl">
              <MapView
                featureCodes={[stateCode]}
                selectedCode={stateCode}
                showLabels
                className="mx-auto max-h-[620px]"
              />
            </div>
          </div>

          <aside className="relative z-20 mx-6 mb-6 rounded-lg border border-slate-200 bg-white p-ui-4 shadow-panel lg:absolute lg:right-6 lg:top-6 lg:mx-0 lg:mb-0 lg:max-h-[700px] lg:w-[350px] lg:overflow-y-auto">
            <p className="text-ui-caption font-ui-semibold uppercase tracking-wide text-slate-500">
              ISO: {stateCode}
            </p>
            <h3 className="mt-ui-1 text-2xl font-ui-semibold text-slate-950">{locale.name}</h3>

            {stateQuery.isLoading ? (
              <p className="mt-5 text-sm text-slate-500">Loading state metrics...</p>
            ) : stateQuery.isError ? (
              <p className="mt-5 text-sm font-medium text-red-600">
                Could not load state metrics.
              </p>
            ) : (
              <div className="mt-ui-4 space-y-ui-4">
                {groupedMeasures.activeMeasure
                  ? renderMeasureCard(groupedMeasures.activeMeasure, true)
                  : null}

                {groupedMeasures.categoryGroups.map((group) => (
                  <section key={group.category} className="border-t border-slate-200 pt-ui-3">
                    <h4 className="mb-ui-2 text-ui-caption font-ui-semibold uppercase tracking-wide text-slate-500">
                      {formatCategoryName(group.category)}
                    </h4>
                    <div className="space-y-ui-2">
                      {group.measures.map((measure) => renderMeasureCard(measure))}
                    </div>
                  </section>
                ))}
              </div>
            )}
          </aside>
        </div>
      </div>
    </section>
  );
}
