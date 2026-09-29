import type { HospitalSummary } from '@/types/hospital';
export default function ScoreBreakdown({hospital}:{hospital:HospitalSummary}) {
  const info=hospital.score_explanation;
  if (!info) return null;
  return <div className="space-y-2"><p className="text-xs text-amber-900">{hospital.score_freshness?.summary || "Score reporting dates unavailable"}</p><details className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
    <summary className="cursor-pointer font-semibold text-compass-950">{info.coverage_pct}% weighted data coverage · {info.overall_score==null?'Not enough data':info.sufficient_data?'Score explained':'Limited data — score explained'}</summary>
    <p className="mt-3 text-slate-600">Coverage is the share of your selected priorities with available data, not a quality rating. Missing measures are excluded; the remaining weights are rescaled to 100%. Hospitals below 50% coverage follow better-documented hospitals in score-sorted lists. Nearby results remain sorted by distance.</p>
    <div className="mt-3 space-y-3">{info.components.map(c=><div key={c.key} className="border-t border-slate-100 pt-3">
      <p className="font-medium">{c.label}: {c.value==null?'Not reported':`${c.value} ${c.unit}`}</p>
      <p className="text-slate-600">Chosen weight {(c.requested_weight*100).toFixed(0)} · Applied weight {(c.effective_weight*100).toFixed(1)}% · {c.requested_weight===0?'Not selected':!c.available?'Excluded — missing data':`${c.contribution?.toFixed(2)} score points`}</p>
      {c.available && c.requested_weight>0 && <div className="mt-1 text-xs text-slate-600">
        {c.period_end ? <p>Reporting period: {c.period_start || 'Start unavailable'} – {c.period_end}{c.date_status==='older_period'?' · Over 2 years old':''}</p> : <p>{c.date_status==='calculated'?'Calculated distance':`Clinical reporting period unknown${c.release_date?`; CMS release ${c.release_date}`:''}`}</p>}
        {c.source_note && <p>{c.source_note}</p>}
        {c.source_url && <a href={c.source_url} target="_blank" rel="noreferrer" className="underline">Source{c.measure_id?` · ${c.measure_id}`:''}</a>}
      </div>}
      {c.available && c.requested_weight>0 && <p className="text-xs text-slate-500">{c.formula} = {c.score?.toFixed(2)}; multiplied by the applied weight.</p>}
    </div>)}</div>
    <p className="mt-4 font-semibold">Total: {info.overall_score==null?'Not enough data':`${info.overall_score.toFixed(1)} / 100`}</p>
    <p className="mt-2 text-xs text-slate-500">Historical data and prototype normalization caps; this score is a preference aid, not a validated clinical recommendation. Displayed contributions may differ slightly from the rounded total.</p>
  </details></div>;
}
