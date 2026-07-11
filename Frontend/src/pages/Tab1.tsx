import { useAnalyticsQuery } from "../api/queries";

const demoStates = ["MH", "GJ"];

export function Tab1() {
  const analyticsQuery = useAnalyticsQuery(demoStates, true);

  return (
    <section className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Tab 1</p>
        <h2 className="text-2xl font-semibold text-slate-950">National Map Explorer</h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Phase 3 connectivity check. The map is built in Phase 4 after the backend API is verified.
        </p>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-slate-950">Live API call</h3>
            <p className="text-sm text-slate-600">GET /api/v1/analytics?states=MH,GJ&amp;include_rank=true</p>
          </div>
          <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
            Census 2011
          </span>
        </div>

        {analyticsQuery.isLoading && <p className="mt-4 text-sm text-slate-600">Loading backend data...</p>}

        {analyticsQuery.isError && (
          <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">
            Unable to reach the backend API. Start FastAPI on port 8000 and try again.
          </p>
        )}

        {analyticsQuery.data && (
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {analyticsQuery.data.data.map((locale) => (
              <article key={locale.locale_code} className="rounded-md border border-slate-200 p-4">
                <div className="flex items-center justify-between">
                  <h4 className="font-semibold text-slate-950">
                    [{locale.locale_code}] {locale.locale_name}
                  </h4>
                  <span className="text-sm text-slate-500">{locale.measures.length} measures</span>
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  {locale.measures.slice(0, 4).map((measure) => (
                    <div key={measure.measure_code}>
                      <dt className="text-slate-500">{measure.measure_name}</dt>
                      <dd className="font-medium text-slate-950">
                        {measure.value.toLocaleString()} {measure.unit}
                      </dd>
                    </div>
                  ))}
                </dl>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
