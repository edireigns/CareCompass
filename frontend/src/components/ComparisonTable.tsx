import type { HospitalDetail } from "@/types/hospital";

const rows: { label: string; get: (h: HospitalDetail) => string | number }[] = [
  { label: "Overall Score", get: (h) => h.overall_score?.toFixed(1) ?? "Not enough data" },
  { label: "Score reporting dates", get: h=>h.score_freshness?.summary || "Unknown" },
  { label: "Weighted data coverage", get: h=>h.score_explanation ? `${h.score_explanation.coverage_pct}%${h.score_explanation.sufficient_data?'':' (limited data)'}` : 'Unknown' },
  { label: "CMS Overall Rating", get: (h) => (h.quality?.cms_overall_rating ? `${h.quality.cms_overall_rating} / 5` : "—") },
  { label: "Patient Satisfaction", get: (h) => (h.experience?.overall_satisfaction != null ? `${h.experience.overall_satisfaction}%` : "—") },
  { label: "Hospital-wide readmission rate", get: (h) => (h.outcomes?.readmission_rate != null ? `${h.outcomes.readmission_rate}%` : "—") },
  { label: "Hospital-wide mortality rate", get: (h) => (h.outcomes?.mortality_rate != null ? `${h.outcomes.mortality_rate}%` : "—") },
  { label: "Hip/knee replacement complications", get: (h) => (h.outcomes?.complication_rate != null ? `${h.outcomes.complication_rate}%` : "—") },
  { label: "ED duration (historical median)", get: (h) => (h.wait_time?.er_wait_minutes != null ? `${h.wait_time.er_wait_minutes} min` : "—") },
  { label: "Distance", get: (h) => (h.distance_miles != null ? `${h.distance_miles} mi` : "—") },
];

export default function ComparisonTable({ hospitals }: { hospitals: HospitalDetail[] }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-compass-100">
      <table className="min-w-full bg-white text-sm">
        <thead>
          <tr className="bg-compass-100 text-compass-950">
            <th className="text-left px-4 py-3 font-semibold">Metric</th>
            {hospitals.map((h) => (
              <th key={h.id} className="text-left px-4 py-3 font-semibold">{h.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-t border-compass-100">
              <td className="px-4 py-3 text-compass-700">{row.label}</td>
              {hospitals.map((h) => (
                <td key={h.id} className="px-4 py-3">{row.get(h)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
