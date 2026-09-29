import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { RankingWeights } from '@/types/hospital';
import type { Point } from '@/components/LocationInput';
import type { SearchParams } from '@/hooks/useHospitals';

export const DEFAULT_WEIGHTS: RankingWeights = {quality:.35,wait_time:.25,distance:0,satisfaction:.1,readmission:.1};
const KEY='carecompass.preferences.v1';
type SearchState = {initialQuery:string; city:string; zip:string; specialty:string; insurance:string; carrier:string; emergency:boolean; mode:string; radius:number; submitted:boolean; params:SearchParams};
export const EMPTY_SEARCH: SearchState = {initialQuery:'',city:'',zip:'',specialty:'',insurance:'',carrier:'',emergency:false,mode:'directory',radius:25,submitted:false,params:{}};
type Selection = {id:string; name:string};
type Preferences = {weights:RankingWeights; point?:Point; search:SearchState; compared:Selection[]};
const defaults=():Preferences=>({weights:{...DEFAULT_WEIGHTS},search:{...EMPTY_SEARCH,params:{}},compared:[]});
function restore():Preferences {
  try {
    const raw=JSON.parse(sessionStorage.getItem(KEY)||'null');
    if (!raw) return defaults();
    const result=defaults();
    if (raw.weights && Object.keys(DEFAULT_WEIGHTS).every(k=>Number.isFinite(raw.weights[k]) && raw.weights[k]>=0 && raw.weights[k]<=1)) result.weights=raw.weights;
    if (raw.point && Number.isFinite(raw.point.lat) && Math.abs(raw.point.lat)<=90 && Number.isFinite(raw.point.lon) && Math.abs(raw.point.lon)<=180) result.point=raw.point;
    if (!result.point) result.weights.distance=0;
    if (raw.search && ['city','zip','specialty','insurance'].every(k=>typeof raw.search[k]==='string')) {
      const s=raw.search;
      result.search={initialQuery:typeof s.initialQuery==="string"?s.initialQuery:"",city:s.city,zip:s.zip,specialty:s.specialty,insurance:s.insurance,carrier:typeof s.carrier==='string'?s.carrier:'',emergency:s.emergency===true,mode:s.mode==='nearby'?'nearby':'directory',radius:[5,10,25,50,100,200].includes(s.radius)?s.radius:25,submitted:s.submitted===true,params:{}};
      const p=s.params;
      if (p && ['city','zip','specialty','insurance'].every(k=>p[k]===undefined||typeof p[k]==='string')) result.search.params={city:p.city,zip:p.zip,specialty:p.specialty,insurance:p.insurance,carrier:typeof p.carrier==='string'?p.carrier:undefined,emergency_only:p.emergency_only===true};
    }
    if (Array.isArray(raw.compared)) result.compared=raw.compared.filter((h:Selection)=>typeof h?.id==='string'&&typeof h?.name==='string').slice(0,5);
    return result;
  } catch { return defaults(); }
}
type Context = {preferences:Preferences; setWeights:(w:RankingWeights)=>void; setPoint:(p?:Point)=>void; setSearch:(s:Partial<SearchState>)=>void; toggleCompared:(h:Selection)=>void; reset:()=>void};
const PreferencesContext=createContext<Context|null>(null);
export function PreferencesProvider({children}:{children:ReactNode}) {
  const [preferences,set]=useState(restore);
  useEffect(()=>{try {sessionStorage.setItem(KEY,JSON.stringify(preferences));} catch {/* Session still works in memory when storage is blocked. */}},[preferences]);
  const value:Context={preferences,
    setWeights:weights=>set(p=>({...p,weights})),
    setPoint:point=>set(p=>({...p,point,weights:point?p.weights:{...p.weights,distance:0}})),
    setSearch:search=>set(p=>({...p,search:{...p.search,...search}})),
    toggleCompared:h=>set(p=>({...p,compared:p.compared.some(x=>x.id===h.id)?p.compared.filter(x=>x.id!==h.id):p.compared.length<5?[...p.compared,h]:p.compared})),
    reset:()=>set(defaults()),
  };
  return <PreferencesContext.Provider value={value}>{children}</PreferencesContext.Provider>;
}
export function usePreferences() {
  const context=useContext(PreferencesContext);
  if (!context) throw new Error('PreferencesProvider is missing');
  return context;
}
export function useRankingParams() {
  const {preferences:{weights,point}}=usePreferences();
  return {...weights,distance:point?weights.distance:0,...point};
}
