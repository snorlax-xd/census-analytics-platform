import { MapView } from "../components/MapView";

export function Tab1() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-8">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Tab 1</p>
        <h2 className="text-2xl font-semibold text-slate-950">National Map Explorer</h2>
        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Data as of Census 2011, using 2011-era state and Union Territory boundaries.
        </p>
      </div>

      <MapView />
    </section>
  );
}
