import { usePreferences } from "@/context/Preferences";
import ScoreBreakdown from "@/components/ScoreBreakdown";
import { useCompare } from "@/hooks/useHospitals";
import ComparisonTable from "@/components/ComparisonTable";

export default function ComparePage() {
  const {preferences,toggleCompared}=usePreferences();
  const ids=preferences.compared.map(h=>h.id);
  const { data: hospitals, isLoading, isError } = useCompare(ids);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl text-compass-950 mb-4">Compare hospitals</h1>
      <p className="text-compass-700 text-sm mb-4">
        Add 2–5 hospitals from search results, rankings, or their profiles. Scores use your saved priorities and location.
      </p>
      <ul className="mb-6 space-y-2">{preferences.compared.map(h=><li key={h.id} className="flex justify-between gap-4 rounded-lg bg-slate-100 p-3 text-sm"><span>{h.name}</span><button className="text-compass-700 underline" onClick={()=>toggleCompared(h)}>Remove</button></li>)}</ul>

      {ids.length >= 2 && isLoading && <p className="text-compass-700">Loading comparison…</p>}
      {isError && <p className="text-signal-600">Couldn't load one or more hospitals.</p>}
      {ids.length>=2 && hospitals && hospitals.length > 0 && <><ComparisonTable hospitals={hospitals} /><div className="mt-6 space-y-4">{hospitals.map(h=><section key={h.id}><h2 className="mb-2 font-semibold">{h.name}</h2><ScoreBreakdown hospital={h} /></section>)}</div></>}
    </div>
  );
}
