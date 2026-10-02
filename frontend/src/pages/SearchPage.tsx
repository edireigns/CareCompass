import CoveragePanel from "@/components/CoveragePanel";
import { usePreferences, EMPTY_SEARCH } from "@/context/Preferences";
import { useEffect, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { useHospitalSearch, useNearby } from "@/hooks/useHospitals";
import HospitalCard from "@/components/HospitalCard";
import LocationInput from "@/components/LocationInput";

export default function SearchPage() {
  const [url] = useSearchParams(); const initial = url.get("q") || "";
  const {preferences:{search:filters,point},setSearch,setPoint}=usePreferences();
  const {city,zip,specialty,insurance,carrier,emergency,mode,radius,submitted,params}=filters;
  useEffect(()=>{ if (initial && initial!==filters.initialQuery) {
    const isZip=/^\d{5}$/.test(initial);
    const params={city:isZip?undefined:initial,zip:isZip?initial:undefined};
    setSearch({...EMPTY_SEARCH,initialQuery:initial,city:params.city||'',zip:params.zip||'',submitted:true,params});
  } },[initial]);
  const setCity=(city:string)=>setSearch({city}); const setZip=(zip:string)=>setSearch({zip});
  const setSpecialty=(specialty:string)=>setSearch({specialty}); const setInsurance=(insurance:string)=>setSearch({insurance});
  const setEmergency=(emergency:boolean)=>setSearch({emergency}); const setMode=(mode:string)=>setSearch({mode});
  const setRadius=(radius:number)=>setSearch({radius});
  const directory = useHospitalSearch(params, submitted && mode === "directory");
  const nearby = useNearby(mode === "nearby" ? point : undefined, radius);
  const query = mode === "nearby" ? nearby : directory;
  const results = mode === "nearby" ? (point ? (emergency ? query.data?.filter(h => h.emergency_services) : query.data) : undefined) : (submitted ? query.data : undefined);
  const { data: specialties = [] } = useQuery({ queryKey: ["specialties"], queryFn: async () => (await apiClient.get<string[]>("/specialties")).data });
  const { data: plans = [] } = useQuery({ queryKey: ["insurance"], queryFn: async () => (await apiClient.get<string[]>("/insurance")).data });
  const {data: categories=[]}=useQuery({queryKey:['insurance-categories'],queryFn:async()=>(await apiClient.get<{carrier:string;plans:string[]}[]>('/insurance/categories')).data});
  const visiblePlans=carrier ? categories.find(c=>c.carrier===carrier)?.plans||[] : plans;
  function search(e:FormEvent) { e.preventDefault(); setSearch({submitted:true,params:{city:city.trim()||undefined,zip:zip||undefined,specialty:specialty||undefined,insurance:insurance||undefined,carrier:carrier||undefined,emergency_only:emergency||undefined}}); }
  function clear() { setSearch({...EMPTY_SEARCH}); }
  return <div className="page-shell">
    <p className="section-kicker">Hospital directory</p><h1 className="page-title mt-2">Find care near you.</h1>
    <p className="page-intro">Search hospitals using public data, then open a profile to see the measures, sources, and reporting dates behind each result.</p>
    <div className="mt-9 grid items-start gap-8 lg:grid-cols-[310px_minmax(0,1fr)]">
      <aside className="space-y-4">
        <div className="flex gap-2 rounded-2xl border border-[#dce6ed] bg-white p-1.5 shadow-card"><button type="button" className={`flex-1 ${mode === "directory" ? "primary-button" : "secondary-button border-transparent shadow-none"}`} onClick={() => setMode("directory")}>City or ZIP</button><button type="button" className={`flex-1 ${mode === "nearby" ? "primary-button" : "secondary-button border-transparent shadow-none"}`} onClick={() => setMode("nearby")}>Nearby</button></div>
        {mode === "nearby" ? <><LocationInput point={point} onChange={setPoint} /><label className="block text-sm font-semibold">Search radius<select className="form-input mt-2" value={radius} onChange={e => setRadius(Number(e.target.value))}>{[5,10,25,50,100,200].map(n => <option key={n} value={n}>{n} miles</option>)}</select></label><p className="text-xs text-slate-500">Only hospitals with verified coordinates from Census address matching or official hospital locations are included. Unmatched addresses are excluded, not placed at estimated city centers.</p></> :
          <form onSubmit={search} className="surface-card space-y-4 p-5 sm:p-6">
            <div><p className="section-kicker">Refine your search</p><h2 className="mt-1 font-display text-xl text-compass-950">Filters</h2></div>
            <label className="block text-sm font-semibold">City<input className="form-input mt-2" value={city} onChange={e => setCity(e.target.value)} /></label>
            <label className="block text-sm font-semibold">ZIP code<input className="form-input mt-2" inputMode="numeric" value={zip} onChange={e => setZip(e.target.value.replace(/\D/g, "").slice(0,5))} /></label>
            <label className="block text-sm font-semibold">Specialty category<select className="form-input mt-2" value={specialty} onChange={e => setSpecialty(e.target.value)}><option value="">All specialty categories</option>{specialty && !specialties.includes(specialty) && <option value={specialty}>{specialty} (saved source name)</option>}{specialties.map(s => <option key={s}>{s}</option>)}</select></label>
            <label className="block text-sm font-semibold">Insurance carrier<select className="form-input mt-2" value={carrier} onChange={e=>setSearch({carrier:e.target.value,insurance:''})}><option value="">All carriers</option>{categories.map(c=><option key={c.carrier}>{c.carrier}</option>)}</select></label>
            <label className="block text-sm font-semibold">Exact verified plan<select className="form-input mt-2" disabled={!plans.length} value={insurance} onChange={e => setInsurance(e.target.value)}><option value="">{plans.length ? "Any plan / unknown" : "No verified plans imported"}</option>{visiblePlans.map(s => <option key={s}>{s}</option>)}</select></label>
            <p className="text-xs text-slate-500">Carrier groups help you browse; they do not establish coverage for every plan. Exact plan names, networks, tiers and years remain separate. No listed plan means unknown coverage.</p>
            <label className="flex items-center gap-3 rounded-xl bg-[#f5f9fb] p-3 text-sm font-semibold text-compass-950"><input type="checkbox" className="h-4 w-4 accent-compass-700" checked={emergency} onChange={e => setEmergency(e.target.checked)} />Emergency services only</label>
            <button className="primary-button w-full" type="submit">Search hospitals</button>
          </form>}
        {mode === "nearby" && <label className="flex gap-2 text-sm"><input type="checkbox" checked={emergency} onChange={e => setEmergency(e.target.checked)} />Emergency services only</label>}
        <button type="button" className="px-2 text-sm font-semibold text-compass-700 hover:underline" onClick={clear}>Clear filters</button>
      </aside>
      <section aria-live="polite" className="min-w-0">
        {city.trim().toLowerCase()==='chicago' && <CoveragePanel compact />}
        <div className="mb-5 flex flex-wrap items-end justify-between gap-3"><div><p className="section-kicker">Explore the directory</p><h2 className="mt-1 font-display text-2xl text-compass-950">{results ? `${results.length} hospitals found` : "Search results"}</h2></div>{results && <span className="text-xs text-[#617986]">Select a hospital to inspect its data</span>}</div>
        {mode === "directory" && !submitted && <p className="surface-card p-6 text-sm text-[#526b79]">Enter a city or ZIP, select a filter, or search the directory.</p>}
        {mode === "nearby" && !point && <p className="surface-card p-6 text-sm text-[#526b79]">Set your location to find nearby hospitals.</p>}
        {query.isFetching && <p className="mb-4 text-compass-700">Loading hospitals…</p>}
        {query.isError && <p role="alert" className="mb-4 text-rose-700">Hospital results could not be loaded. Please try again.</p>}
        {results?.length === 0 && <p className="surface-card p-6 text-sm text-[#526b79]">No hospitals matched. Try a larger radius or fewer filters.</p>}
        {mode === "directory" && results && results.length >= 500 && <p className="mb-4 text-sm text-slate-500">Showing the first 500 matches. Narrow your search to see more specific results.</p>}
        <div className="grid gap-5 xl:grid-cols-2">{results?.map(h => <HospitalCard key={h.id} hospital={h} />)}</div>
      </section>
    </div>
  </div>;
}
