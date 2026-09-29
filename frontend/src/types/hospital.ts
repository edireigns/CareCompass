// Mirrors backend/app/schemas/hospital.py — keep these in sync manually
// for now; a shared OpenAPI-generated client is a natural upgrade later.

export interface Location {
  address_line1?: string | null;
  city?: string | null;
  state?: string | null;
  zip_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
}

export interface Quality {
  cms_overall_rating?: number | null;
  quality_of_care_rating?: number | null;
  safety_rating?: number | null;

  mortality_group_measure_count?: number | null;
  mortality_facility_measure_count?: number | null;
  mortality_better?: number | null;
  mortality_no_different?: number | null;
  mortality_worse?: number | null;

  safety_group_measure_count?: number | null;
  safety_facility_measure_count?: number | null;
  safety_better?: number | null;
  safety_no_different?: number | null;
  safety_worse?: number | null;

  readmission_group_measure_count?: number | null;
  readmission_facility_measure_count?: number | null;
  readmission_better?: number | null;
  readmission_no_different?: number | null;
  readmission_worse?: number | null;
}

export interface Outcomes {
  readmission_rate?: number;
  mortality_rate?: number;
  infection_rate?: number;
  complication_rate?: number;
}

export interface Experience {
  overall_satisfaction?: number;
  would_recommend_pct?: number;
  communication_score?: number;
  cleanliness_score?: number;
}

export interface WaitTime {
  er_wait_minutes?: number | null;
  appointment_wait_days?: number | null;
}

export interface ScoreExplanation {
  overall_score: number | null;
  coverage_pct: number;
  sufficient_data: boolean;
  components: {key:string;label:string;value:number|null;unit:string;available:boolean;requested_weight:number;effective_weight:number;score:number|null;contribution:number|null;formula:string;date_status:string;measure_id?:string;period_start?:string;period_end?:string;release_date?:string;source_url?:string;source_note?:string}[];
}

export interface HospitalSummary {
  id: string;
  name: string;
  cms_presence?: {present:boolean;checked_on:string;release_date?:string|null}|null;
  hospital_type?: string | null;
  emergency_services: boolean ;
  trauma_level?: string | null;
  teaching_hospital: boolean;
  pediatric_hospital: boolean;
  location?: Location | null;
  quality?: Quality | null;
  wait_time?: WaitTime | null;
  distance_miles?: number | null;
  overall_score?: number | null;
  score_explanation?: ScoreExplanation | null;
  score_freshness?: {summary:string;older_measure_count:number;unknown_period_count:number;oldest_period_end?:string;newest_period_end?:string}|null;
}

export interface HospitalDetail extends HospitalSummary {
  cms_provider_id?: string | null;
  ownership_type?: string | null;
  outcomes?: Outcomes | null;
  experience?: Experience | null;
  specialties: string[];
  insurance_plans: string[];
  measures: { freshness: string; measure_id: string; source_key: string; name: string; value: number; unit: string; comparison?: string; period_start?: string; period_end?: string; source_url: string }[];
  directory_entries: { search_category:string; freshness: string; kind: string; name: string; source_url: string; source_label: string; verified_on: string; expires_on?: string }[];
}

export interface RankingWeights {
  quality: number;
  wait_time: number;
  distance: number;
  satisfaction: number;
  readmission: number;
}

export interface RecommendResponse {
  answer: string;
  supporting_hospitals: HospitalSummary[];
  disclaimer: string;
}
