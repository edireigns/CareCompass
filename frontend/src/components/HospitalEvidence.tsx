import type { HospitalDetail } from "@/types/hospital";

export default function HospitalEvidence({ hospital }: { hospital: HospitalDetail }) {
  const today = new Date().toISOString().slice(0, 10);
  return <div className="space-y-8">
    <p className={hospital.cms_presence?.present === false ? "rounded-xl bg-amber-50 p-4 text-amber-900" : "text-sm text-slate-600"}>
      {hospital.cms_presence ? `${hospital.cms_presence.present ? "Listed" : "Not listed"} in the latest imported CMS directory (checked ${hospital.cms_presence.checked_on}${hospital.cms_presence.release_date ? `; release ${hospital.cms_presence.release_date}` : "; release date unavailable"}).${hospital.cms_presence.present ? "" : " Operating status is unconfirmed; absence does not establish closure."}` : "Latest CMS directory membership has not been verified."}
    </p>
    <section className="surface-card p-5 sm:p-6">
      <h2 className="font-display text-2xl text-compass-950">Detailed measures and reporting periods</h2>
      <p className="mt-2 text-sm text-slate-600">CMS reports historical results for specific patient groups. Infection ratios compare observed with expected infections; they are not percentages. ED duration is time spent in the emergency department, not a live wait estimate.</p>
      {hospital.measures?.length ? <div className="mt-5 space-y-3">{hospital.measures.map(m => <details key={`${m.source_key}-${m.measure_id}`} className="rounded-xl border border-[#e2ebef] bg-[#f8fbfc] p-4 open:bg-white">
        <summary className="cursor-pointer font-medium text-slate-800">{m.name}: <strong>{m.value} {m.unit}</strong>{m.freshness === "older_period" && <span className="ml-2 text-xs text-amber-800">Older reporting period</span>}{m.freshness === "unknown" && <span className="ml-2 text-xs text-slate-500">Date unavailable</span>}</summary>
        <p className="mt-2 text-sm text-amber-800">{m.freshness === "older_period" ? "Older reporting period — ended more than 2 years ago" : m.freshness === "unknown" ? "Reporting date unavailable" : m.freshness === "future_period" ? "Reporting end date is in the future — review source" : "Reporting period ended within the last 2 years"}</p>
        <p className="mt-2 text-sm text-slate-600">Reporting period: {m.period_start || "Not supplied"} – {m.period_end || "Not supplied"}</p>
        {m.comparison && <p className="text-sm text-slate-600">{m.comparison}</p>}
        <a className="mt-2 inline-block text-sm text-compass-700 underline" href={m.source_url} target="_blank" rel="noreferrer">CMS source · {m.measure_id}</a>
      </details>)}</div> : <p className="mt-4 text-slate-500">No reportable measures are available for this hospital. Missing or suppressed values are not treated as zero.</p>}
    </section>
    <section className="surface-card p-5 sm:p-6">
      <h2 className="font-display text-2xl text-compass-950">Insurance and specialty sources</h2>
      <p className="mt-2 text-sm text-slate-600">Insurance networks depend on the exact plan and date. Unknown does not mean a plan is rejected. Confirm coverage for your facility, clinician, service and date with the insurer. A hospital listing does not establish physician participation. CMS hospital-type specialties describe facility classification.</p>
      {hospital.directory_entries?.length ? <ul className="mt-4 space-y-3">{hospital.directory_entries.map(e => <li key={`${e.kind}-${e.name}`} className="rounded-xl border border-[#e2ebef] bg-[#f8fbfc] p-4 text-sm">
        <strong>{e.name}</strong> · {e.kind === "insurance" ? "Insurance record" : "Specialty record"}
        {e.expires_on && e.expires_on < today && <span className="ml-2 text-amber-800">Expired — not shown as currently accepted</span>}
        {e.freshness === "review_due" && <p className="text-amber-800">Recheck recommended — verified more than 180 days ago. Current participation is unconfirmed.</p>}
        <p className="mt-1 text-slate-600">Search category: {e.search_category} · Original source name preserved above</p>
        <p className="mt-1">Checked {e.verified_on}{e.expires_on ? ` · Expires ${e.expires_on}` : " · No expiry supplied"}</p>
        <a className="text-compass-700 underline" href={e.source_url} target="_blank" rel="noreferrer">{e.source_label}</a>
      </li>)}</ul> : <p className="mt-4 text-slate-500">No verified directory records have been imported for this hospital.</p>}
    </section>
  </div>;
}
