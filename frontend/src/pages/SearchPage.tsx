import { FormEvent, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useHospitalSearch } from "@/hooks/useHospitals";
import HospitalCard from "@/components/HospitalCard";

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const initialQuery = searchParams.get("q") ?? "";
  const [city, setCity] = useState(initialQuery.match(/^\d{5}$/) ? "" : initialQuery);
  const [zip, setZip] = useState(initialQuery.match(/^\d{5}$/) ? initialQuery : "");
  const [emergencyOnly, setEmergencyOnly] = useState(false);
  const [submitted, setSubmitted] = useState(Boolean(initialQuery));

  const params = useMemo(
    () => ({
      city: submitted && city.trim() ? city.trim() : undefined,
      zip: submitted && zip.trim() ? zip.trim() : undefined,
      emergency_only: submitted && emergencyOnly ? true : undefined,
    }),
    [city, zip, emergencyOnly, submitted],
  );

  const { data: hospitals, isLoading, isError } = useHospitalSearch(params);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitted(true);
  }

  function clearFilters() {
    setCity("");
    setZip("");
    setEmergencyOnly(false);
    setSubmitted(false);
  }

  return (
    <div className="min-h-full bg-slate-50">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8">
          <p className="section-kicker">Hospital directory</p>
          <h1 className="mt-2 font-display text-4xl text-compass-950">Find hospitals that match your needs.</h1>
          <p className="mt-3 max-w-2xl text-slate-600">
            Search by location and narrow results using emergency-service availability.
          </p>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-8 px-5 py-8 lg:grid-cols-[280px_1fr] lg:px-8">
        <aside>
          <form onSubmit={handleSubmit} className="sticky top-24 rounded-2xl border border-slate-200 bg-white p-5 shadow-card">
            <div className="flex items-center justify-between">
              <h2 className="font-display text-2xl text-compass-950">Filters</h2>
              <button type="button" onClick={clearFilters} className="text-sm font-medium text-compass-700 hover:text-compass-950">
                Clear
              </button>
            </div>

            <label className="mt-6 block text-sm font-semibold text-slate-700">
              City
              <input
                value={city}
                onChange={(event) => setCity(event.target.value)}
                placeholder="Example: New York"
                className="form-input mt-2"
              />
            </label>

            <label className="mt-5 block text-sm font-semibold text-slate-700">
              ZIP code
              <input
                value={zip}
                onChange={(event) => setZip(event.target.value.replace(/\D/g, "").slice(0, 5))}
                placeholder="10001"
                inputMode="numeric"
                className="form-input mt-2"
              />
            </label>

            <label className="mt-5 flex cursor-pointer items-start gap-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={emergencyOnly}
                onChange={(event) => setEmergencyOnly(event.target.checked)}
                className="mt-1 h-4 w-4 rounded border-slate-300 text-compass-700 focus:ring-compass-500"
              />
              <span>
                <strong className="block">Emergency services only</strong>
                <span className="mt-1 block text-xs leading-5 text-slate-500">Show hospitals that report emergency services.</span>
              </span>
            </label>

            <button type="submit" className="primary-button mt-6 w-full">Search hospitals</button>
          </form>
        </aside>

        <section>
          <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-compass-500">Results</p>
              <h2 className="mt-1 font-display text-3xl text-compass-950">
                {hospitals ? `${hospitals.length} hospitals found` : "Search results"}
              </h2>
            </div>
            <p className="text-sm text-slate-500">Data provided for informational use.</p>
          </div>

          {!submitted && (
            <div className="rounded-2xl border border-dashed border-compass-300 bg-compass-100/50 p-10 text-center">
              <h3 className="font-display text-2xl text-compass-950">Start with a city or ZIP code.</h3>
              <p className="mx-auto mt-3 max-w-md text-slate-600">Use the filters to search the CMS hospital directory.</p>
            </div>
          )}

          {submitted && isLoading && (
            <div className="grid gap-5 md:grid-cols-2">
              {[1, 2, 3, 4].map((item) => <div key={item} className="h-64 animate-pulse rounded-2xl bg-slate-200" />)}
            </div>
          )}

          {submitted && isError && (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
              The hospital service could not be reached. Confirm that the backend is running on port 8000.
            </div>
          )}

          {submitted && !isLoading && hospitals?.length === 0 && (
            <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center shadow-card">
              <h3 className="font-display text-2xl text-compass-950">No hospitals matched these filters.</h3>
              <p className="mt-3 text-slate-600">Try a nearby city, a different ZIP code, or remove the emergency-only filter.</p>
            </div>
          )}

          <div className="grid gap-5 md:grid-cols-2">
            {hospitals?.map((hospital) => <HospitalCard key={hospital.id} hospital={hospital} />)}
          </div>
        </section>
      </div>
    </div>
  );
}
