import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const features = [
  {
    title: "Start with your location",
    description: "Search by city or ZIP code, then refine by emergency services and available specialty or plan records.",
  },
  {
    title: "Compare what matters",
    description: "Review ratings and outcomes side by side instead of choosing only by distance.",
  },
  {
    title: "Understand every score",
    description: "See public CMS measures, weighted data coverage, source links, and reporting dates in plain language.",
  },
];

export default function LandingPage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const value = query.trim();
    navigate(value ? `/search?q=${encodeURIComponent(value)}` : "/search");
  }

  return (
    <div>
      <section className="relative overflow-hidden border-b border-[#dce6ed] bg-[#edf5f8]">
        <div className="absolute inset-0 bg-hero-pattern" />
        <div className="absolute inset-y-0 right-0 hidden w-[46%] subtle-grid opacity-60 lg:block" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-5 py-16 sm:py-20 lg:grid-cols-[1.08fr_0.92fr] lg:gap-16 lg:px-8 lg:py-28">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-[#bed9e5] bg-white/75 px-4 py-2 text-xs font-bold uppercase tracking-[0.13em] text-compass-700 shadow-sm">
              <span className="h-2 w-2 rounded-full bg-[#32a18f]" /> Public hospital data, made clearer
            </span>
            <h1 className="mt-7 max-w-3xl font-display text-5xl font-semibold leading-[1.06] tracking-tight text-compass-950 sm:text-6xl lg:text-[4.4rem]">
              Find care with <span className="text-compass-700">clarity.</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-[#4a6474]">
              Explore hospitals, compare quality measures, and see where the data is incomplete. Make a more informed decision with the evidence in view.
            </p>

            <form onSubmit={handleSubmit} className="mt-9 flex max-w-xl flex-col gap-3 rounded-2xl border border-[#d5e3e9] bg-white p-2.5 shadow-card-hover sm:flex-row">
              <input
                aria-label="City or ZIP code"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by city or ZIP code"
                className="min-h-12 min-w-0 flex-1 rounded-xl border-0 px-4 text-compass-950 outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-compass-300"
              />
              <button className="primary-button whitespace-nowrap" type="submit">
                Find hospitals <span aria-hidden="true">→</span>
              </button>
            </form>

            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-xs font-semibold text-[#597485]">
              <span>✓ Nationwide directory</span>
              <span>✓ Public CMS measures</span>
              <span>✓ Free to explore</span>
            </div>
          </div>

          <div className="relative mx-auto w-full max-w-md lg:ml-auto">
            <div className="absolute -right-6 -top-6 h-40 w-40 rounded-full border border-[#b5d6e3] opacity-70" aria-hidden="true" />
            <div className="absolute -right-14 -top-14 h-56 w-56 rounded-full border border-[#b5d6e3] opacity-50" aria-hidden="true" />
            <div className="surface-card relative overflow-hidden p-6 sm:p-8">
              <div className="flex items-center justify-between gap-4">
                <span className="section-kicker">A clearer view of care</span>
                <span className="grid h-10 w-10 place-items-center rounded-full bg-compass-100 text-xl text-compass-700" aria-hidden="true">✦</span>
              </div>
              <h2 className="mt-5 font-display text-3xl leading-tight text-compass-950">The details behind the decision.</h2>
              <div className="mt-7 space-y-3">
                {[
                  ["01", "Search by place", "Find hospitals by city, ZIP, or location."],
                  ["02", "Set your priorities", "Adjust ranking weights to match what matters."],
                  ["03", "Check the evidence", "See data coverage, sources, and reporting dates."],
                ].map(([number, title, detail]) => <div key={number} className="flex gap-4 rounded-xl border border-[#e2ebef] bg-[#f8fbfc] p-4">
                  <span className="font-display text-xl text-compass-500">{number}</span>
                  <div><strong className="text-sm text-compass-950">{title}</strong><p className="mt-1 text-xs leading-5 text-[#5b7280]">{detail}</p></div>
                </div>)}
              </div>
              <p className="mt-5 text-xs leading-5 text-[#617986]">Measures may reflect older reporting periods. CareCompass shows that context beside each score.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-20 lg:px-8">
        <div className="max-w-2xl">
          <p className="section-kicker">How CareCompass helps</p>
          <h2 className="mt-3 font-display text-4xl text-compass-950">Useful answers, with the context that matters.</h2>
        </div>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {features.map((feature, index) => (
            <div key={feature.title} className="surface-card p-7 transition duration-200 hover:-translate-y-1 hover:shadow-card-hover">
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-compass-100 font-display text-lg font-semibold text-compass-700">0{index + 1}</span>
              <h3 className="mt-5 font-display text-2xl text-compass-950">{feature.title}</h3>
              <p className="mt-3 leading-7 text-slate-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 px-5 py-12 md:flex-row md:items-center lg:px-8">
          <div>
            <p className="section-kicker">Need help deciding?</p>
            <h2 className="mt-2 font-display text-3xl text-compass-950">Ask CareCompass to explain your options.</h2>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/assistant" className="primary-button">Ask the AI assistant</Link>
            <Link to="/rankings" className="secondary-button">Explore rankings</Link>
          </div>
        </div>
      </section>
    </div>
  );
}
