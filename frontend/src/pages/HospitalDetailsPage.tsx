import ScoreBreakdown from "@/components/ScoreBreakdown";
import { usePreferences } from "@/context/Preferences";
import HospitalEvidence from "@/components/HospitalEvidence";
import { useParams } from "react-router-dom";

import { useHospitalDetail } from "@/hooks/useHospitals";


function MetricRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 py-3 last:border-0">
      <dt className="text-slate-600">{label}</dt>
      <dd className="text-right font-semibold text-compass-950">{value}</dd>
    </div>
  );
}


function PerformanceGroup({
  title,
  measureCount,
  better,
  noDifferent,
  worse,
}: {
  title: string;
  measureCount?: number | null;
  better?: number | null;
  noDifferent?: number | null;
  worse?: number | null;
}) {
  const hasData = [measureCount, better, noDifferent, worse].some(
    (value) => value !== null && value !== undefined,
  );

  return (
    <article className="surface-card p-5">
      <h3 className="font-display text-xl text-compass-950">{title}</h3>

      {!hasData ? (
        <p className="mt-4 text-sm text-slate-500">
          CMS performance details were not reported for this hospital.
        </p>
      ) : (
        <>
          <p className="mt-2 text-sm text-slate-500">
            Based on {measureCount ?? 0} reported facility measures
          </p>

          <div className="mt-5 grid grid-cols-3 gap-2 text-center">
            <div className="rounded-xl bg-emerald-50 p-3">
              <p className="text-2xl font-bold text-emerald-700">
                {better ?? 0}
              </p>
              <p className="mt-1 text-xs text-emerald-800">Better</p>
            </div>

            <div className="rounded-xl bg-slate-100 p-3">
              <p className="text-2xl font-bold text-slate-700">
                {noDifferent ?? 0}
              </p>
              <p className="mt-1 text-xs text-slate-600">No different</p>
            </div>

            <div className="rounded-xl bg-rose-50 p-3">
              <p className="text-2xl font-bold text-rose-700">
                {worse ?? 0}
              </p>
              <p className="mt-1 text-xs text-rose-800">Worse</p>
            </div>
          </div>
        </>
      )}
    </article>
  );
}


function formatValue(
  value: number | null | undefined,
  suffix = "",
): string {
  return value === null || value === undefined
    ? "Not reported"
    : `${value}${suffix}`;
}


export default function HospitalDetailsPage() {
  const {preferences,toggleCompared}=usePreferences();
  const { id } = useParams<{ id: string }>();
  const {
    data: hospital,
    isLoading,
    isError,
  } = useHospitalDetail(id);

  if (!Object.values(preferences.weights).some(w=>w>0)) return <p className="p-6">Choose at least one priority above zero using Adjust priorities.</p>;
  if (isLoading) {
    return (
      <p className="mx-auto max-w-6xl px-6 py-10 text-compass-700">
        Loading hospital profile...
      </p>
    );
  }

  if (isError || !hospital) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-rose-800">
          This hospital profile could not be loaded.
        </div>
      </div>
    );
  }

  const address = [
    hospital.location?.address_line1,
    hospital.location?.city,
    hospital.location?.state,
    hospital.location?.zip_code,
  ]
    .filter(Boolean)
    .join(", ");

  return (
    <div className="min-h-full bg-[#f6f8fb]">
      <section className="border-b border-[#dce6ed] bg-[#edf5f8]">
        <div className="mx-auto max-w-6xl px-5 py-10 sm:py-14 lg:px-8">
          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-start">
            <div>
              <p className="section-kicker">
                Hospital profile
              </p>

              <h1 className="page-title mt-2 max-w-2xl">
                {hospital.name}
              </h1>

              <p className="mt-3 text-[#536b7a]">
                {address || "Location not reported"}
              </p>

              <div className="mt-5 flex flex-wrap gap-2">
                {hospital.emergency_services && (
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-sm font-semibold text-rose-800">
                    Emergency services
                  </span>
                )}

                {hospital.hospital_type && (
                  <span className="rounded-full bg-compass-100 px-3 py-1 text-sm font-semibold text-compass-800">
                    {hospital.hospital_type}
                  </span>
                )}

                {hospital.teaching_hospital && (
                  <span className="rounded-full bg-indigo-100 px-3 py-1 text-sm font-semibold text-indigo-800">
                    Teaching hospital
                  </span>
                )}

                {hospital.pediatric_hospital && (
                  <span className="rounded-full bg-amber-100 px-3 py-1 text-sm font-semibold text-amber-800">
                    Pediatric hospital
                  </span>
                )}
              </div>
            </div>

            <div className="grid min-w-0 grid-cols-2 gap-3 sm:min-w-[360px]">
              <div className="rounded-2xl bg-compass-950 p-4 text-white shadow-card sm:p-5">
                <p className="text-sm text-compass-100">CareCompass Score</p>
                <p className="mt-2 text-4xl font-bold">
                  {hospital.overall_score?.toFixed(1) ?? "N/A"}
                </p>
                <p className="mt-1 text-xs text-compass-200">Out of 100</p>
              </div>

              <div className="rounded-2xl border border-[#dce6ed] bg-white p-4 shadow-card sm:p-5">
                <p className="text-sm text-slate-500">CMS Overall Rating</p>
                <p className="mt-2 text-4xl font-bold text-compass-950">
                  {hospital.quality?.cms_overall_rating ?? "N/A"}
                </p>
                <p className="mt-1 text-xs text-slate-500">Out of 5 stars</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl space-y-8 px-5 py-10 lg:px-8">
        <button className="secondary-button disabled:opacity-50" disabled={!preferences.compared.some(h=>h.id===hospital.id)&&preferences.compared.length>=5} onClick={()=>toggleCompared({id:hospital.id,name:hospital.name})}>{preferences.compared.some(h=>h.id===hospital.id)?'Remove from comparison':'Add to comparison'}</button>
        <ScoreBreakdown hospital={hospital} />
        <section>
          <h2 className="font-display text-2xl text-compass-950">
            Hospital information
          </h2>

          <dl className="surface-card mt-4 grid gap-x-8 px-5 md:grid-cols-2">
            <MetricRow
              label="CMS Facility ID"
              value={hospital.cms_provider_id || "Not reported"}
            />
            <MetricRow
              label="Ownership"
              value={hospital.ownership_type || "Not reported"}
            />
            <MetricRow
              label="Hospital type"
              value={hospital.hospital_type || "Not reported"}
            />
            <MetricRow
              label="Emergency services"
              value={hospital.emergency_services ? "Available" : "Not reported"}
            />
            <MetricRow
              label="Trauma level"
              value={hospital.trauma_level || "Not reported"}
            />
            <MetricRow
              label="Address"
              value={address || "Not reported"}
            />
          </dl>
        </section>

        <section>
          <h2 className="font-display text-2xl text-compass-950">
            CMS performance summary
          </h2>

          <p className="mt-2 max-w-3xl text-sm text-slate-600">
            These counts show how this hospital performed compared with the
            national benchmark across available CMS measures.
          </p>

          <div className="mt-4 grid gap-5 lg:grid-cols-3">
            <PerformanceGroup
              title="Mortality"
              measureCount={
                hospital.quality?.mortality_facility_measure_count
              }
              better={hospital.quality?.mortality_better}
              noDifferent={hospital.quality?.mortality_no_different}
              worse={hospital.quality?.mortality_worse}
            />

            <PerformanceGroup
              title="Safety"
              measureCount={
                hospital.quality?.safety_facility_measure_count
              }
              better={hospital.quality?.safety_better}
              noDifferent={hospital.quality?.safety_no_different}
              worse={hospital.quality?.safety_worse}
            />

            <PerformanceGroup
              title="Readmission"
              measureCount={
                hospital.quality?.readmission_facility_measure_count
              }
              better={hospital.quality?.readmission_better}
              noDifferent={hospital.quality?.readmission_no_different}
              worse={hospital.quality?.readmission_worse}
            />
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-2">
          <section className="surface-card p-5">
            <h2 className="font-display text-2xl text-compass-950">
              Clinical outcomes
            </h2>

            <dl className="mt-3 text-sm">
              <MetricRow
                label="Hospital-wide readmission rate"
                value={formatValue(
                  hospital.outcomes?.readmission_rate,
                  "%",
                )}
              />
              <MetricRow
                label="Hospital-wide mortality rate"
                value={formatValue(
                  hospital.outcomes?.mortality_rate,
                  "%",
                )}
              />

              <MetricRow
                label="Hip/knee replacement complications"
                value={formatValue(
                  hospital.outcomes?.complication_rate,
                  "%",
                )}
              />
            </dl>
          </section>

          <section className="surface-card p-5">
            <h2 className="font-display text-2xl text-compass-950">
              Patient experience
            </h2>

            <dl className="mt-3 text-sm">
              <MetricRow
                label="Overall satisfaction"
                value={formatValue(
                  hospital.experience?.overall_satisfaction,
                  "%",
                )}
              />
              <MetricRow
                label="Would recommend"
                value={formatValue(
                  hospital.experience?.would_recommend_pct,
                  "%",
                )}
              />
              <MetricRow
                label="Nurses always communicated well (%)"
                value={formatValue(
                  hospital.experience?.communication_score,
                )}
              />
              <MetricRow
                label="Room always clean (%)"
                value={formatValue(
                  hospital.experience?.cleanliness_score,
                )}
              />
            </dl>
          </section>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <section>
            <h2 className="font-display text-2xl text-compass-950">
              Specialties
            </h2>

            <div className="mt-4 flex flex-wrap gap-2">
              {hospital.specialties.length > 0 ? (
                hospital.specialties.map((specialty) => (
                  <span
                    key={specialty}
                    className="rounded-full bg-compass-100 px-3 py-1 text-sm text-compass-800"
                  >
                    {specialty}
                  </span>
                ))
              ) : (
                <p className="text-sm text-slate-500">
                  Specialty information is not currently available.
                </p>
              )}
            </div>
          </section>

          <section>
            <h2 className="font-display text-2xl text-compass-950">
              Insurance accepted
            </h2>

            <div className="mt-4 flex flex-wrap gap-2">
              {hospital.insurance_plans.length > 0 ? (
                hospital.insurance_plans.map((insurance) => (
                  <span
                    key={insurance}
                    className="rounded-full bg-compass-100 px-3 py-1 text-sm text-compass-800"
                  >
                    {insurance}
                  </span>
                ))
              ) : (
                <p className="text-sm text-slate-500">
                  Coverage unknown — no current verified plans have been imported.
                </p>
              )}
            </div>
          </section>
        </div>

        <HospitalEvidence hospital={hospital} />
        <p className="border-t border-slate-200 pt-6 text-xs leading-5 text-slate-500">
          CareCompass presents public CMS data for informational purposes.
          Ratings and performance measures are not medical advice. Contact the
          hospital to confirm current services and insurance coverage.
        </p>
      </div>
    </div>
  );
}
