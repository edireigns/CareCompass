import { useState } from "react";
import { useRankings } from "@/hooks/useHospitals";
import HospitalCard from "@/components/HospitalCard";
import RankingWeightSliders from "@/components/RankingWeightSliders";
import type { RankingWeights } from "@/types/hospital";

const DEFAULT_WEIGHTS: RankingWeights = {
  quality: 0.35,
  wait_time: 0.25,
  distance: 0.2,
  satisfaction: 0.1,
  readmission: 0.1,
};

export default function RankingsPage() {
  const [weights, setWeights] = useState<RankingWeights>(DEFAULT_WEIGHTS);
  // NOTE: scaffold calls /rankings with default weights; wire `weights` into
  // the query params (see api/routes/rankings.py) once the slider UI is final.
  const { data: hospitals, isLoading } = useRankings(10);

  return (
    <div className="max-w-5xl mx-auto px-6 py-10">
      <h1 className="font-display text-2xl text-compass-950 mb-6">Top-ranked hospitals</h1>
      <div className="grid md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <RankingWeightSliders weights={weights} onChange={setWeights} />
        </div>
        <div className="md:col-span-2 space-y-4">
          {isLoading && <p className="text-compass-700">Loading rankings…</p>}
          {hospitals?.map((h) => (
            <HospitalCard key={h.id} hospital={h} />
          ))}
        </div>
      </div>
    </div>
  );
}
