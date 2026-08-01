import { useState } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/search", label: "Find care" },
  { to: "/rankings", label: "Rankings" },
  { to: "/compare", label: "Compare" },
  { to: "/assistant", label: "AI assistant" },
  { to: "/analytics", label: "Insights" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-compass-950/95 text-white backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 lg:px-8">
        <NavLink to="/" className="flex items-center gap-3" onClick={() => setOpen(false)}>
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-white/10 text-lg font-bold">+</span>
          <span>
            <span className="block font-display text-xl leading-none">CareCompass</span>
            <span className="mt-1 block text-[11px] uppercase tracking-[0.18em] text-compass-300">
              Better care decisions
            </span>
          </span>
        </NavLink>

        <button
          type="button"
          className="rounded-lg border border-white/15 px-3 py-2 text-sm md:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-label="Toggle navigation"
        >
          {open ? "Close" : "Menu"}
        </button>

        <nav className="hidden items-center gap-1 md:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-white/10 text-white"
                    : "text-compass-100 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          <NavLink
            to="/search"
            className="ml-3 rounded-lg bg-signal-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-signal-600"
          >
            Search hospitals
          </NavLink>
        </nav>
      </div>

      {open && (
        <nav className="border-t border-white/10 px-5 pb-5 pt-3 md:hidden">
          <div className="grid gap-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-3 text-sm font-medium ${
                    isActive ? "bg-white/10 text-white" : "text-compass-100"
                  }`
                }
              >
                {link.label}
              </NavLink>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
