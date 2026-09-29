import {useQuery} from '@tanstack/react-query';
import {Link} from 'react-router-dom';
import {apiClient} from '@/api/client';
type Coverage={scope:string;total:number;coordinates:number;insurance_hospitals:number;clinical_specialty_hospitals:number;reviewed_hospitals:number;hospitals:{id:string;facility_id:string;name:string;coordinates:boolean;insurance_records:number;clinical_specialty_records:number;review?:{checked_on:string;note:string;sources:string[]}}[]};
export default function CoveragePanel({compact=false}:{compact?:boolean}) {
 const {data,isError}=useQuery({queryKey:['chicago-coverage'],queryFn:async()=>(await apiClient.get<Coverage>('/data/coverage/chicago')).data});
 if(!data) return isError?<p className="text-sm text-slate-500">Chicago coverage could not be loaded.</p>:null;
 return <section className={`${compact ? "mb-4" : "mb-6"} space-y-3 rounded-2xl border border-slate-200 bg-white p-5`}>
  <h2 className="font-display text-xl text-compass-950">Chicago verified coverage</h2>
  <p className="text-xs text-slate-500">{data.scope}</p>
  <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">{[['Coordinates',data.coordinates],['At least one sourced plan',data.insurance_hospitals],['Clinical specialties',data.clinical_specialty_hospitals],['Source checks recorded',data.reviewed_hospitals]].map(([label,count])=><div key={label}><strong className="block text-xl">{count}/{data.total}</strong>{label}</div>)}</div>
  <p className="text-xs text-slate-600">Coverage counts hospitals with at least one record, not complete plan or service lists. Zero means unknown. Clinical specialties exclude CMS facility classifications. Source checks can leave records unknown, including inaccessible or outdated sources.</p>
  <details><summary className="cursor-pointer text-sm font-semibold text-compass-700">Review hospital-by-hospital coverage</summary><div className="mt-3 overflow-x-auto"><table className="min-w-full text-left text-xs"><thead><tr>{['Hospital','Coordinates','Plan records','Clinical records','Source review'].map(h=><th className="p-2" key={h}>{h}</th>)}</tr></thead><tbody>{data.hospitals.map(h=><tr key={h.id} className="border-t border-slate-100"><td className="p-2"><Link className="underline" to={`/hospital/${h.id}`}>{h.name}</Link><p>{h.facility_id}</p></td><td className="p-2">{h.coordinates?'Matched':'Unknown'}</td><td className="p-2">{h.insurance_records||'Unknown'}</td><td className="p-2">{h.clinical_specialty_records||'Unknown'}</td><td className="min-w-64 p-2">{h.review?<><p>Checked {h.review.checked_on}</p><p>{h.review.note}</p>{h.review.sources.map((url,i)=><a key={url} className="mr-2 underline" href={url} target="_blank" rel="noreferrer">Source {i+1}</a>)}</>:'Not reviewed yet'}</td></tr>)}</tbody></table></div></details>
 </section>;
}
