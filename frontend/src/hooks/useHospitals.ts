import { useQuery, useMutation } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import type { HospitalSummary, HospitalDetail, RecommendResponse } from "@/types/hospital";

export interface SearchParams {
  city?: string;
  zip?: string;
  specialty?: string;
  emergency_only?: boolean;
  lat?: number;
  lon?: number;
}

export function useHospitalSearch(params: SearchParams) {
  return useQuery({
    queryKey: ["hospitals", "search", params],
    queryFn: async () => {
      console.log("API base URL:", apiClient.defaults.baseURL);
      console.log("Search parameters:", params);

      const { data } = await apiClient.get<HospitalSummary[]>("/search", { params });
      console.log("Hospital results:", data);
      return data;
    },
    enabled: Object.values(params).some((v) => v !== undefined && v !== ""),
  });
}

export function useHospitalDetail(id: string | undefined) {
  return useQuery({
    queryKey: ["hospital", id],
    queryFn: async () => {
      const { data } = await apiClient.get<HospitalDetail>(`/hospital/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useRankings(limit = 10) {
  return useQuery({
    queryKey: ["rankings", limit],
    queryFn: async () => {
      const { data } = await apiClient.get<HospitalSummary[]>("/rankings", { params: { limit } });
      return data;
    },
  });
}

export function useCompare(ids: string[]) {
  return useQuery({
    queryKey: ["compare", ids],
    queryFn: async () => {
      const { data } = await apiClient.get<HospitalDetail[]>("/compare", {
        params: { ids },
        paramsSerializer: { indexes: null }, // ids=a&ids=b, not ids[0]=a
      });
      return data;
    },
    enabled: ids.length >= 2,
  });
}

export function useRecommend() {
  return useMutation({
    mutationFn: async (payload: { question: string; zip_code?: string; latitude?: number; longitude?: number }) => {
      const { data } = await apiClient.post<RecommendResponse>("/recommend", payload);
      return data;
    },
  });
}
