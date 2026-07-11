import { useParams } from "react-router-dom";

export function StateDetail() {
  const { id } = useParams();

  return (
    <section className="mx-auto max-w-6xl px-6 py-8">
      <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Tab 1 focused route</p>
      <h2 className="mt-1 text-2xl font-semibold text-slate-950">State detail: {id?.toUpperCase()}</h2>
      <p className="mt-2 text-sm text-slate-600">
        Focused state map and stats panel are scheduled for Phase 4.
      </p>
    </section>
  );
}
