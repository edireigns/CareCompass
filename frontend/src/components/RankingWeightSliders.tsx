import type { RankingWeights } from "@/types/hospital";

const fields: { key: keyof RankingWeights; label: string }[] = [
  { key: "quality", label: "Quality Rating" },
  { key: "wait_time", label: "ED visit duration (historical)" },
  { key: "distance", label: "Distance" },
  { key: "satisfaction", label: "Patient Satisfaction" },
  { key: "readmission", label: "Readmission Performance" },
];

export default function RankingWeightSliders({
  weights,
  onChange,
  hasLocation = false,
}: {
  hasLocation?: boolean;
  weights: RankingWeights;
  onChange: (w: RankingWeights) => void;
}) {
  const total = Object.values(weights).reduce((sum, v) => sum + v, 0);

  return (
    <div className="bg-white rounded-xl border border-compass-100 p-5 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-compass-950">Customize your priorities</h3>
        <span className={`text-xs ${Math.abs(total - 1) > 0.01 ? "text-signal-600" : "text-compass-500"}`}>
          Total: {(total * 100).toFixed(0)}%
        </span>
      </div>
      {fields.map(({ key, label }) => (
        <div key={key}>
          <div className="flex justify-between text-sm text-compass-700 mb-1">
            <span>{label}</span>
            <span>{Math.round(weights[key] * 100)}%</span>
          </div>
          <input
            type="range"
            aria-label={label}
            disabled={key === "distance" && !hasLocation}
            min={0}
            max={1}
            step={0.05}
            value={weights[key]}
            onChange={(e) => onChange({ ...weights, [key]: parseFloat(e.target.value) })}
            className="w-full accent-compass-500"
          />
          {key === "distance" && !hasLocation && <p className="text-xs text-slate-500">Set a location to include distance.</p>}
        </div>
      ))}
    </div>
  );
}
