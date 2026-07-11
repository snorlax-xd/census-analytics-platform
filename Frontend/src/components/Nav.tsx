import { NavLink } from "react-router-dom";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  [
    "rounded-md px-3 py-2 text-sm font-medium transition",
    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950",
  ].join(" ");

export function Nav() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">Census 2011</p>
          <h1 className="text-xl font-semibold text-slate-950">Census Analytics Platform</h1>
        </div>
        <nav className="flex gap-2">
          <NavLink to="/tab1" className={navLinkClass}>
            Tab 1
          </NavLink>
          <NavLink to="/tab2" className={navLinkClass}>
            Tab 2
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
