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
  return <div className="page-shell">
    <p className="section-kicker">Your priorities, your view</p>
    <h1 className="page-title mt-2">Hospital rankings.</h1>
    <p className="page-intro mb-8">Adjust priorities to recalculate results. Missing measures are excluded, and hospitals with at least 50% weighted data coverage appear first. Open a score to see its calculation and reporting dates.</p>
    <div className="grid items-start gap-8 lg:grid-cols-[310px_minmax(0,1fr)]">
      <aside className="space-y-4">
        <RankingWeightSliders weights={weights} onChange={setWeights} hasLocation={!!point} />
        <LocationInput point={point} onChange={setPoint} />
        <button type="button" className="secondary-button w-full" onClick={() => setWeights(DEFAULT_WEIGHTS)}>Reset priorities</button>
      </aside>
      <section aria-live="polite" className="min-w-0 space-y-5">
        <div className="surface-card px-5 py-4 text-sm text-[#536b7a]">Historical ED duration is not a current wait estimate. Scores are preference aids based on available public measures.</div>
        {!valid && <p className="rounded-xl bg-amber-50 p-4 text-amber-800">Set at least one priority above zero.</p>}
        {valid && isFetching && <p className="text-compass-700">Updating rankings…</p>}
        {valid && isError && <p role="alert" className="text-rose-700">Rankings could not be loaded. Please try again.</p>}
        {valid && data?.map(h => <HospitalCard key={h.id} hospital={h} />)}
      </section>
    </div>
  </div>;
}
