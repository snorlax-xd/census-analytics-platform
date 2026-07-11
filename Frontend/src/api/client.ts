import axios from "axios";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1",
});

export type MeasureValue = {
  measure_code: string;
  measure_name: string;
  category: string;
  unit: string;
  value: number;
  higher_is_better: boolean | null;
  rank: number | null;
};

export type LocaleAnalytics = {
  locale_code: string;
  locale_name: string;
  year: number;
  measures: MeasureValue[];
};

export type AnalyticsResponse = {
  data: LocaleAnalytics[];
};

export async function getAnalytics(params: {
  states: string[];
  year?: number;
  includeRank?: boolean;
}): Promise<AnalyticsResponse> {
  const response = await apiClient.get<AnalyticsResponse>("/analytics", {
    params: {
      states: params.states.join(","),
      year: params.year ?? 2011,
      include_rank: params.includeRank ?? false,
    },
  });

  return response.data;
}
