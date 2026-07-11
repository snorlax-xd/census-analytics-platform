import { useQuery } from "@tanstack/react-query";

import { getAnalytics } from "./client";

export function useAnalyticsQuery(states: string[], includeRank = false) {
  return useQuery({
    queryKey: ["analytics", states, 2011, includeRank],
    queryFn: () => getAnalytics({ states, year: 2011, includeRank }),
    enabled: states.length > 0,
  });
}
