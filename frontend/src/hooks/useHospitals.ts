import { useRankingParams } from "@/context/Preferences";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { HospitalSummary, HospitalDetail, RecommendResponse, RankingWeights } from "@/types/hospital";

const validWeights=(w:RankingWeights)=>[w.quality,w.wait_time,w.distance,w.satisfaction,w.readmission].some(v=>v>0);

export interface SearchParams {
  city?: string;
  zip?: string;
  specialty?: string;
  insurance?: string;
  carrier?: string;
  emergency_only?: boolean;
  lat?: number;
  lon?: number;
}

export function useHospitalSearch(params: SearchParams, enabled = true) {
  const ranking=useRankingParams();
  const combined={...params,...ranking};
  return useQuery({
    queryKey: ["hospitals", "search", combined],
    staleTime: 60_000,
    queryFn: async () => {


      const { data } = await apiClient.get<HospitalSummary[]>("/search", { params:combined });

      return data;
    },
    enabled:enabled && validWeights(ranking),
  });
}

export function useHospitalDetail(id: string | undefined) {
  const ranking=useRankingParams();
  return useQuery({
    queryKey: ["hospital", id, ranking],
    staleTime: 60_000,
    queryFn: async () => {
      const { data } = await apiClient.get<HospitalDetail>(`/hospital/${id}`, {params:ranking});
      return data;
    },
    enabled: !!id && validWeights(ranking),
  });
}

export function useRankings(limit = 10, weights?: RankingWeights, point?: { lat: number; lon: number }) {
  const saved=useRankingParams();
  const ranking=weights?{...weights,...point}:saved;
  return useQuery({
    queryKey: ["rankings", limit, ranking],
    staleTime: 60_000,
    enabled: [ranking.quality,ranking.wait_time,ranking.distance,ranking.satisfaction,ranking.readmission].some(v=>v>0),
    queryFn: async () => {
      const { data } = await apiClient.get<HospitalSummary[]>("/rankings", { params: { limit, ...ranking } });
      return data;
    },
  });
}

export function useCompare(ids: string[]) {
  const ranking=useRankingParams();
  return useQuery({
    queryKey: ["compare", ids, ranking],
    staleTime: 60_000,
    queryFn: async () => {
      const { data } = await apiClient.get<HospitalDetail[]>("/compare", {
        params: { ids, ...ranking },
        paramsSerializer: { indexes: null }, // ids=a&ids=b, not ids[0]=a
      });
      return data;
    },
    enabled: ids.length >= 2 && validWeights(ranking),
  });
}

export interface RecommendPayload{
  question: string;
  city?: string;
  state?: string;
  zip_code?: string;
  latitude?: number;
  longitude?: number;
}

export function useRecommend() {
  return useMutation({
    mutationFn: async (payload: RecommendPayload) => {
      const { data } = await apiClient.post<RecommendResponse>("/recommend", payload);
      return data;
    },
  });
}

export function useNearby(point?: { lat: number; lon: number }, radius = 25) {
  const ranking=useRankingParams();
  return useQuery({ queryKey: ["nearby", point, radius, ranking], staleTime: 60_000, queryFn: async () => {
    const { data } = await apiClient.get<HospitalSummary[]>("/nearby", { params: { ...ranking, ...point, radius_miles: radius } }); return data;
  }, enabled: !!point && validWeights(ranking) });
}
