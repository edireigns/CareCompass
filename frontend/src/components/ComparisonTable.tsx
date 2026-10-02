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
    <div className="surface-card overflow-x-auto">
      <table className="min-w-full bg-white text-sm">
        <thead>
          <tr className="bg-compass-950 text-white">
            <th scope="col" className="min-w-44 text-left px-5 py-4 font-semibold">Metric</th>
            {hospitals.map((h) => (
              <th scope="col" key={h.id} className="min-w-52 text-left px-5 py-4 font-semibold">{h.name}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label} className="border-t border-[#e5edf1] even:bg-[#f8fbfc]">
              <th scope="row" className="px-5 py-4 text-left font-semibold text-compass-900">{row.label}</th>
              {hospitals.map((h) => (
                <td key={h.id} className="px-5 py-4 text-[#4b6473]">{row.get(h)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
