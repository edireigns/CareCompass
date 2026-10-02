import { usePreferences } from "@/context/Preferences";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import { useCompare } from "@/hooks/useHospitals";
import ComparisonTable from "@/components/ComparisonTable";

export default function ComparePage() {
  const {preferences,toggleCompared}=usePreferences();
  const ids=preferences.compared.map(h=>h.id);
  const { data: hospitals, isLoading, isError } = useCompare(ids);

  return (
    <div className="page-shell max-w-6xl">
      <p className="section-kicker">Side by side</p>
      <h1 className="page-title mb-4 mt-2">Compare hospitals.</h1>
      <p className="page-intro mb-8">
        Add 2–5 hospitals from search results, rankings, or their profiles. Scores use your saved priorities and location.
      </p>
      <ul className="mb-6 grid gap-3 sm:grid-cols-2">{preferences.compared.map(h=><li key={h.id} className="surface-card flex items-center justify-between gap-4 p-4 text-sm"><span className="font-semibold text-compass-950">{h.name}</span><button className="font-semibold text-compass-700 hover:underline" onClick={()=>toggleCompared(h)}>Remove</button></li>)}</ul>
      {ids.length < 2 && <p className="surface-card p-6 text-sm text-[#536b7a]">Add at least two hospitals from search or rankings to see a comparison.</p>}

      {ids.length >= 2 && isLoading && <p className="text-compass-700">Loading comparison…</p>}
      {isError && <p className="text-signal-600">Couldn't load one or more hospitals.</p>}
      {ids.length>=2 && hospitals && hospitals.length > 0 && <><ComparisonTable hospitals={hospitals} /><div className="mt-6 space-y-4">{hospitals.map(h=><section key={h.id}><h2 className="mb-2 font-semibold">{h.name}</h2><ScoreBreakdown hospital={h} /></section>)}</div></>}
    </div>
  );
}
