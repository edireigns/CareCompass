import { useState } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/search", label: "Find care" },
  { to: "/rankings", label: "Rankings" },
  { to: "/compare", label: "Compare" },
  { to: "/assistant", label: "AI assistant" },
  { to: "/analytics", label: "Insights" },
  { to: "/admin", label: "Data Refresh" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-[#dce6ed] bg-white/95 text-compass-950 shadow-[0_3px_18px_rgba(16,45,64,0.035)] backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-5 px-5 py-3.5 lg:px-8">
        <NavLink to="/" className="flex shrink-0 items-center gap-3" onClick={() => setOpen(false)}>
          <span className="relative grid h-11 w-11 place-items-center rounded-[14px] bg-compass-950 text-xl text-white shadow-sm" aria-hidden="true">✦</span>
          <span>
            <span className="block font-display text-xl font-semibold leading-none tracking-tight">CareCompass</span>
            <span className="mt-1 block text-[10px] font-bold uppercase tracking-[0.16em] text-compass-700">
              Clarity for care
            </span>
          </span>
        </NavLink>

        <button
          type="button"
          className="rounded-lg border border-[#cbd8e2] px-3 py-2 text-sm font-semibold lg:hidden"
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-label="Toggle navigation"
        >
          {open ? "Close" : "Menu"}
        </button>

        <nav aria-label="Main navigation" className="hidden items-center gap-0.5 lg:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-lg px-2.5 py-2 text-sm font-semibold transition-colors lg:px-3 ${
                  isActive
                    ? "bg-compass-100 text-compass-950"
                    : "text-[#526b79] hover:bg-[#f2f7f9] hover:text-compass-950"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </div>

      {open && (
        <nav aria-label="Mobile navigation" className="border-t border-[#dce6ed] bg-white px-5 pb-5 pt-3 lg:hidden">
          <div className="grid gap-1">
            {links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `rounded-lg px-3 py-3 text-sm font-semibold ${
                    isActive ? "bg-compass-100 text-compass-950" : "text-[#526b79] hover:bg-[#f2f7f9]"
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
