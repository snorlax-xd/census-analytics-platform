import { scaleQuantile } from "d3-scale";

export type LegendBucket = {
  color: string;
  min: number;
  max: number;
};

const CHOROPLETH_COLORS = [
  "#e8f3f1",
  "#c8e4df",
  "#96cec6",
  "#5fb0aa",
  "#2f8688",
  "#195a66",
];

export function createChoroplethScale(values: number[]) {
  const finiteValues = values.filter(Number.isFinite);

  if (finiteValues.length === 0) {
    return {
      colorForValue: () => "#e2e8f0",
      buckets: [] as LegendBucket[],
    };
  }

  const scale = scaleQuantile<string>()
    .domain(finiteValues)
    .range(CHOROPLETH_COLORS);

  const sortedValues = [...finiteValues].sort((a, b) => a - b);
  const min = sortedValues[0];
  const max = sortedValues[sortedValues.length - 1];
  const thresholds = scale.quantiles();
  const stops = [min, ...thresholds, max];

  return {
    colorForValue: (value: number | null | undefined) =>
      typeof value === "number" && Number.isFinite(value) ? scale(value) : "#e2e8f0",
    buckets: CHOROPLETH_COLORS.map((color, index) => ({
      color,
      min: stops[index],
      max: stops[index + 1],
    })),
  };
}
