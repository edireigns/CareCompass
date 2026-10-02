import ScoreBreakdown from "./ScoreBreakdown";
import { usePreferences } from "@/context/Preferences";
import { Link } from "react-router-dom";
import type { HospitalSummary } from "@/types/hospital";

function ScoreBadge({
  score,
}: {
  score?: number | null;
}) {
  if (score == null || !Number.isFinite(score)) {
    return (
      <span className="flex min-w-20 flex-col items-center rounded-xl bg-[#f2f5f7] px-3 py-2 text-center text-xs font-semibold text-[#607786]">
        <span className="text-sm">No score</span>
      </span>
    );
  }

  const tone = score >= 75 ? "bg-emerald-50 text-emerald-800" : score >= 50 ? "bg-compass-100 text-compass-900" : "bg-amber-50 text-amber-900";

  return (
    <span
      className={`${tone} flex min-w-20 flex-col items-center rounded-xl px-3 py-2 text-center`}
    >
      <strong className="text-xl leading-none">{score.toFixed(1)}</strong>
      <small className="mt-1 text-[10px] font-bold uppercase tracking-wider">Score</small>
    </span>
  );
}

export default function HospitalCard({
  hospital,
}: {
  hospital: HospitalSummary;
}) {
  const {preferences,toggleCompared}=usePreferences();
  const selected=preferences.compared.some(h=>h.id===hospital.id);
  const city = hospital.location?.city;
  const state = hospital.location?.state;

  return (
    <article className="surface-card overflow-hidden transition duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
    <Link
      to={`/hospital/${hospital.id}`}
      className="group block p-5 sm:p-6"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h3 className="text-lg font-bold leading-snug text-compass-950 transition-colors group-hover:text-compass-700">
            {hospital.name}
          </h3>

          <p className="mt-2 text-sm text-[#526b79]">
            {city || state
              ? `${city ?? ""}${city && state ? ", " : ""}${state ?? ""}`
              : "Location unavailable"}

            {hospital.distance_miles != null &&
              Number.isFinite(hospital.distance_miles) &&
              ` · ${hospital.distance_miles.toFixed(1)} miles away`}
          </p>

          <p className="mt-2 text-xs font-medium text-[#6b8290]">
            {hospital.hospital_type || "Hospital type unavailable"}
          </p>

          {hospital.cms_presence?.present === false && <p className="mt-2 text-sm text-amber-800">Not listed in latest imported CMS directory. Operating status unconfirmed.</p>}
          <div className="mt-4 flex flex-wrap gap-2 text-xs">
            {hospital.emergency_services && (
              <span className="care-badge care-badge-positive">
                Emergency services
              </span>
            )}

            {hospital.trauma_level && (
              <span className="care-badge">
                Trauma {hospital.trauma_level}
              </span>
            )}

            {hospital.teaching_hospital && (
              <span className="care-badge">
                Teaching
              </span>
            )}

            {hospital.pediatric_hospital && (
              <span className="care-badge">
                Pediatric
              </span>
            )}

            {hospital.quality?.cms_overall_rating != null && (
              <span className="care-badge">
                CMS rating: {hospital.quality.cms_overall_rating}/5
              </span>
            )}
          </div>
        </div>

        <ScoreBadge score={hospital.overall_score} />
      </div>
    </Link>
    <div className="border-t border-[#e5edf1] px-5 py-4 sm:px-6">
      <ScoreBreakdown hospital={hospital} />
      <button className="mt-3 inline-flex items-center gap-2 text-sm font-bold text-compass-700 hover:text-compass-950 hover:underline disabled:opacity-50" disabled={!selected && preferences.compared.length>=5} onClick={()=>toggleCompared({id:hospital.id,name:hospital.name})}>{selected?"− Remove from comparison":"+ Add to comparison"}</button>
    </div>
    </article>
  );
}
