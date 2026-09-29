import { useEffect, useState } from "react";
import { useRankings } from "@/hooks/useHospitals";
import HospitalCard from "@/components/HospitalCard";
import RankingWeightSliders from "@/components/RankingWeightSliders";
import LocationInput from "@/components/LocationInput";
import { usePreferences, DEFAULT_WEIGHTS } from "@/context/Preferences";


export default function RankingsPage() {
  const {preferences:{weights,point},setWeights,setPoint}=usePreferences();
  const [applied, setApplied] = useState(weights);
  useEffect(() => { const timer = setTimeout(() => setApplied(weights), 300); return () => clearTimeout(timer); }, [weights]);
  const { data, isFetching, isError } = useRankings(10, applied, point);
  const valid = Object.values(weights).some(v => v > 0);
  return <div className="mx-auto max-w-6xl px-6 py-10">
    <h1 className="font-display text-3xl text-compass-950">Top-ranked hospitals</h1>
    <p className="mb-6 mt-3 text-sm text-slate-600">Adjust priorities to recalculate results. Weights are normalized automatically. Missing measures are excluded. Hospitals with at least 50% weighted coverage appear first; expand a score to see its calculation. Historical ED duration is not a current wait estimate.</p>
    <div className="grid gap-6 md:grid-cols-[300px_1fr]">
      <aside className="space-y-4">
        <RankingWeightSliders weights={weights} onChange={setWeights} hasLocation={!!point} />
        <LocationInput point={point} onChange={setPoint} />
        <button type="button" className="secondary-button w-full" onClick={() => setWeights(DEFAULT_WEIGHTS)}>Reset priorities</button>
      </aside>
      <section aria-live="polite" className="space-y-4">
        {!valid && <p className="rounded-xl bg-amber-50 p-4 text-amber-800">Set at least one priority above zero.</p>}
        {valid && isFetching && <p className="text-compass-700">Updating rankings…</p>}
        {valid && isError && <p role="alert" className="text-rose-700">Rankings could not be loaded. Please try again.</p>}
        {valid && data?.map(h => <HospitalCard key={h.id} hospital={h} />)}
      </section>
    </div>
  </div>;
}
