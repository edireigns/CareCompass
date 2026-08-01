import { useParams } from "react-router-dom";
import { useHospitalDetail } from "@/hooks/useHospitals";

export default function HospitalDetailsPage() {
  const { id } = useParams<{ id: string }>();
  const { data: hospital, isLoading, isError } = useHospitalDetail(id);

  if (isLoading) return <p className="max-w-4xl mx-auto px-6 py-10 text-compass-700">Loading…</p>;
  if (isError || !hospital)
    return <p className="max-w-4xl mx-auto px-6 py-10 text-signal-600">Hospital not found.</p>;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <h1 className="font-display text-3xl text-compass-950">{hospital.name}</h1>
      <p className="text-compass-700 mt-1">
        {hospital.location?.city}, {hospital.location?.state} {hospital.location?.zip_code}
      </p>

      <div className="grid md:grid-cols-2 gap-4 mt-8">
        <div className="bg-white rounded-xl border border-compass-100 p-5">
          <h2 className="font-display text-compass-950 mb-3">Quality &amp; Outcomes</h2>
          <dl className="text-sm space-y-2 text-compass-700">
            <div className="flex justify-between"><dt>CMS Overall Rating</dt><dd>{hospital.quality?.cms_overall_rating ?? "—"} / 5</dd></div>
            <div className="flex justify-between"><dt>Readmission Rate</dt><dd>{hospital.outcomes?.readmission_rate ?? "—"}%</dd></div>
            <div className="flex justify-between"><dt>Mortality Rate</dt><dd>{hospital.outcomes?.mortality_rate ?? "—"}%</dd></div>
            <div className="flex justify-between"><dt>Infection Rate</dt><dd>{hospital.outcomes?.infection_rate ?? "—"}</dd></div>
          </dl>
        </div>

        <div className="bg-white rounded-xl border border-compass-100 p-5">
          <h2 className="font-display text-compass-950 mb-3">Patient Experience</h2>
          <dl className="text-sm space-y-2 text-compass-700">
            <div className="flex justify-between"><dt>Overall Satisfaction</dt><dd>{hospital.experience?.overall_satisfaction ?? "—"}%</dd></div>
            <div className="flex justify-between"><dt>Would Recommend</dt><dd>{hospital.experience?.would_recommend_pct ?? "—"}%</dd></div>
            <div className="flex justify-between"><dt>ER Wait Time</dt><dd>{hospital.wait_time?.er_wait_minutes ?? "—"} min</dd></div>
          </dl>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-4">
        <div>
          <h3 className="text-sm font-semibold text-compass-950 mb-2">Specialties</h3>
          <div className="flex flex-wrap gap-2">
            {hospital.specialties.map((s) => (
              <span key={s} className="bg-compass-100 text-compass-700 text-xs rounded px-2 py-1">{s}</span>
            ))}
          </div>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-compass-950 mb-2">Insurance accepted</h3>
          <div className="flex flex-wrap gap-2">
            {hospital.insurance_plans.map((i) => (
              <span key={i} className="bg-compass-100 text-compass-700 text-xs rounded px-2 py-1">{i}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
