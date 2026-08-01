import { Link } from "react-router-dom";
import type { HospitalSummary } from "@/types/hospital";

function ScoreBadge({
  score,
}: {
  score?: number | null;
}) {
  if (score == null || !Number.isFinite(score)) {
    return (
      <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-600">
        Not rated
      </span>
    );
  }

  const tone =
    score >= 75
      ? "bg-emerald-600"
      : score >= 50
        ? "bg-amber-500"
        : "bg-slate-500";

  return (
    <span
      className={`${tone} rounded-full px-3 py-1 text-sm font-semibold text-white`}
    >
      {score.toFixed(0)}
    </span>
  );
}

export default function HospitalCard({
  hospital,
}: {
  hospital: HospitalSummary;
}) {
  const city = hospital.location?.city;
  const state = hospital.location?.state;

  return (
    <Link
      to={`/hospital/${hospital.id}`}
      className="block rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-lg font-semibold text-slate-950">
            {hospital.name}
          </h3>

          <p className="mt-1 text-sm text-slate-600">
            {city || state
              ? `${city ?? ""}${city && state ? ", " : ""}${state ?? ""}`
              : "Location unavailable"}

            {hospital.distance_miles != null &&
              Number.isFinite(hospital.distance_miles) &&
              ` · ${hospital.distance_miles.toFixed(1)} miles away`}
          </p>

          <p className="mt-2 text-sm text-slate-500">
            {hospital.hospital_type || "Hospital type unavailable"}
          </p>

          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            {hospital.emergency_services && (
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 font-medium text-emerald-800">
                Emergency services
              </span>
            )}

            {hospital.trauma_level && (
              <span className="rounded-full bg-slate-100 px-2.5 py-1 text-slate-700">
                Trauma {hospital.trauma_level}
              </span>
            )}

            {hospital.teaching_hospital && (
              <span className="rounded-full bg-blue-100 px-2.5 py-1 text-blue-800">
                Teaching
              </span>
            )}

            {hospital.pediatric_hospital && (
              <span className="rounded-full bg-purple-100 px-2.5 py-1 text-purple-800">
                Pediatric
              </span>
            )}

            {hospital.quality?.cms_overall_rating != null && (
              <span className="rounded-full bg-amber-100 px-2.5 py-1 text-amber-800">
                CMS rating: {hospital.quality.cms_overall_rating}/5
              </span>
            )}
          </div>
        </div>

        <ScoreBadge score={hospital.overall_score} />
      </div>
    </Link>
  );
}