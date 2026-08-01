import type { HospitalDetail } from "@/types/hospital";

const rows: { label: string; get: (h: HospitalDetail) => string | number }[] = [
  { label: "Overall Score", get: (h) => h.overall_score?.toFixed(0) ?? "—" },
  { label: "CMS Overall Rating", get: (h) => (h.quality?.cms_overall_rating ? `${h.quality.cms_overall_rating} / 5` : "—") },
  { label: "Patient Satisfaction", get: (h) => (h.experience?.overall_satisfaction ? `${h.experience.overall_satisfaction}%` : "—") },
  { label: "Readmission Rate", get: (h) => (h.outcomes?.readmission_rate ? `${h.outcomes.readmission_rate}%` : "—") },
  { label: "Mortality Rate", get: (h) => (h.outcomes?.mortality_rate ? `${h.outcomes.mortality_rate}%` : "—") },
  { label: "Infection Rate", get: (h) => (h.outcomes?.infection_rate ? `${h.outcomes.infection_rate}` : "—") },
  { label: "ER Wait Time", get: (h) => (h.wait_time?.er_wait_minutes ? `${h.wait_time.er_wait_minutes} min` : "—") },
  { label: "Distance", get: (h) => (h.distance_miles !== undefined ? `${h.distance_miles} mi` : "—") },
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
