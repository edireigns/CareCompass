// Mirrors backend/app/schemas/hospital.py — keep these in sync manually
// for now; a shared OpenAPI-generated client is a natural upgrade later.

export interface Location {
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

export interface HospitalSummary {
  id: string;
  name: string;
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
}

export interface HospitalDetail extends HospitalSummary {
  outcomes?: Outcomes;
  experience?: Experience;
  specialties: string[];
  insurance_plans: string[];
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
