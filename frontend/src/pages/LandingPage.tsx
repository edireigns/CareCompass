import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

const features = [
  {
    title: "Search smarter",
    description: "Filter hospitals by city, ZIP code, emergency services, hospital type, and CMS quality rating.",
  },
  {
    title: "Compare quality",
    description: "Review ratings and outcomes side by side instead of choosing only by distance.",
  },
  {
    title: "Understand the data",
    description: "See public CMS information presented in plain language that is easier to use.",
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
      <section className="relative overflow-hidden bg-compass-950 text-white">
        <div className="absolute inset-0 bg-hero-pattern opacity-40" />
        <div className="relative mx-auto grid max-w-7xl gap-12 px-5 py-20 lg:grid-cols-[1.2fr_0.8fr] lg:px-8 lg:py-28">
          <div>
            <span className="inline-flex rounded-full border border-compass-300/30 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-compass-100">
              Built with trusted public healthcare data
            </span>
            <h1 className="mt-6 max-w-3xl font-display text-5xl leading-[1.05] tracking-tight sm:text-6xl">
              Find the right hospital with more confidence.
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-compass-100">
              Search more than 5,000 hospitals, compare CMS quality information, and make a better-informed care decision.
            </p>

            <form onSubmit={handleSubmit} className="mt-9 flex max-w-2xl flex-col gap-3 rounded-2xl bg-white p-3 shadow-2xl sm:flex-row">
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search by city or ZIP code"
                className="min-h-12 flex-1 rounded-xl border-0 px-4 text-compass-950 outline-none placeholder:text-slate-400 focus:ring-2 focus:ring-compass-300"
              />
              <button className="min-h-12 rounded-xl bg-signal-500 px-6 font-semibold text-white transition hover:bg-signal-600">
                Find hospitals
              </button>
            </form>

            <div className="mt-6 flex flex-wrap gap-x-6 gap-y-2 text-sm text-compass-100">
              <span>5,432 hospitals</span>
              <span>CMS quality data</span>
              <span>Free public access</span>
            </div>
          </div>

          <div className="hidden items-center justify-center lg:flex">
            <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/10 p-6 shadow-2xl backdrop-blur">
              <div className="rounded-2xl bg-white p-5 text-compass-950">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-compass-500">Example result</p>
                    <h2 className="mt-2 font-display text-2xl">City Medical Center</h2>
                  </div>
                  <span className="rounded-full bg-emerald-100 px-3 py-1 text-sm font-bold text-emerald-800">82 score</span>
                </div>
                <p className="mt-2 text-sm text-slate-600">New York, NY · Acute care hospital</p>
                <div className="mt-5 grid grid-cols-3 gap-3 text-center">
                  <div className="rounded-xl bg-slate-50 p-3"><strong className="block text-lg">4/5</strong><span className="text-xs text-slate-500">CMS rating</span></div>
                  <div className="rounded-xl bg-slate-50 p-3"><strong className="block text-lg">Yes</strong><span className="text-xs text-slate-500">Emergency</span></div>
                  <div className="rounded-xl bg-slate-50 p-3"><strong className="block text-lg">24/7</strong><span className="text-xs text-slate-500">Access</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-16 lg:px-8">
        <div className="max-w-2xl">
          <p className="section-kicker">How CareCompass helps</p>
          <h2 className="mt-3 font-display text-4xl text-compass-950">Better information before an important decision.</h2>
        </div>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {features.map((feature, index) => (
            <div key={feature.title} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-compass-100 font-bold text-compass-700">0{index + 1}</span>
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
