"""
Service layer: orchestrates repositories + business logic (distance
calculation, ranking, comparison, and the AI assistant's grounding step).
Routes call services; services call repositories. Routes never touch
the ORM or the DB session directly.
"""
from typing import Optional
from geopy.distance import geodesic

from app.models.hospital import Hospital
from app.repositories.hospital_repository import HospitalRepository
from app.schemas.hospital import (
    HospitalSummary, HospitalDetail, RankingWeights, RecommendResponse,
)
from app.services.ranking_service import compute_overall_score


class HospitalService:
    def __init__(self, repo: HospitalRepository):
        self.repo = repo

    @staticmethod
    def _distance_miles(hospital: Hospital, lat: Optional[float], lon: Optional[float]) -> Optional[float]:
        if lat is None or lon is None or not hospital.location:
            return None
        if hospital.location.latitude is None or hospital.location.longitude is None:
            return None
        origin = (lat, lon)
        dest = (hospital.location.latitude, hospital.location.longitude)
        return round(geodesic(origin, dest).miles, 1)

    def _to_summary(
        self, hospital: Hospital, weights: RankingWeights,
        user_lat: Optional[float] = None, user_lon: Optional[float] = None,
    ) -> HospitalSummary:
        distance = self._distance_miles(hospital, user_lat, user_lon)
        summary = HospitalSummary.model_validate(hospital)
        summary.distance_miles = distance
        summary.overall_score = compute_overall_score(hospital, weights, distance)
        return summary

    def search(
        self, city=None, zip_code=None, specialty=None, emergency_only=False,
        trauma_level=None, teaching_only=False, pediatric_only=False,
        user_lat=None, user_lon=None, weights: Optional[RankingWeights] = None,
    ) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        hospitals = self.repo.search(
            city=city, zip_code=zip_code, specialty=specialty,
            emergency_only=emergency_only, trauma_level=trauma_level,
            teaching_only=teaching_only, pediatric_only=pediatric_only,
        )
        results = [self._to_summary(h, weights, user_lat, user_lon) for h in hospitals]
        return sorted(results, key=lambda h: h.overall_score or 0, reverse=True)

    def nearby(self, lat: float, lon: float, radius_miles: float = 25, weights: Optional[RankingWeights] = None) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        all_hospitals = self.repo.list_all()
        results = []
        for h in all_hospitals:
            distance = self._distance_miles(h, lat, lon)
            if distance is not None and distance <= radius_miles:
                summary = self._to_summary(h, weights, lat, lon)
                results.append(summary)
        return sorted(results, key=lambda h: h.distance_miles or 9999)

    def get_detail(self, hospital_id: str, weights: Optional[RankingWeights] = None, user_lat=None, user_lon=None) -> Optional[HospitalDetail]:
        weights = weights or RankingWeights()
        hospital = self.repo.get_by_id(hospital_id)
        if not hospital:
            return None
        distance = self._distance_miles(hospital, user_lat, user_lon)
        detail = HospitalDetail.model_validate(hospital)
        detail.distance_miles = distance
        detail.overall_score = compute_overall_score(hospital, weights, distance)
        detail.specialties = [s.name for s in hospital.specialties]
        detail.insurance_plans = [i.name for i in hospital.insurance_plans]
        return detail

    def compare(self, hospital_ids: list[str], weights: Optional[RankingWeights] = None) -> list[HospitalDetail]:
        weights = weights or RankingWeights()
        hospitals = self.repo.get_by_ids(hospital_ids)
        details = []
        for h in hospitals:
            detail = HospitalDetail.model_validate(h)
            detail.overall_score = compute_overall_score(h, weights, None)
            detail.specialties = [s.name for s in h.specialties]
            detail.insurance_plans = [i.name for i in h.insurance_plans]
            details.append(detail)
        return details

    def rankings(self, limit: int = 10, weights: Optional[RankingWeights] = None) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        hospitals = self.repo.list_all(limit=limit * 3)  # over-fetch, then sort + trim
        results = [self._to_summary(h, weights) for h in hospitals]
        return sorted(results, key=lambda h: h.overall_score or 0, reverse=True)[:limit]

    def recommend(self, question: str, zip_code: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None) -> RecommendResponse:
        """
        AI Recommendation Assistant — grounding step only.

        This intentionally does NOT call an LLM in the scaffold. It narrows
        candidate hospitals using the same search/ranking logic used
        elsewhere, so the eventual LLM call only has to *summarize* this
        pre-filtered, factual data rather than invent anything (per spec:
        "The AI should summarize the supporting data rather than invent
        information."). Wire in an Anthropic API call here that receives
        `candidates` as context and produces `answer`.
        """
        weights = RankingWeights()
        if lat is not None and lon is not None:
            candidates = self.nearby(lat, lon, radius_miles=25, weights=weights)[:5]
        else:
            candidates = self.rankings(limit=5, weights=weights)

        answer = (
            f"Based on public CMS quality, outcomes, and wait-time data, here are the "
            f"top {len(candidates)} matches for: \"{question}\". This is a scaffold "
            f"response — connect an LLM call here, passing `candidates` as grounding "
            f"context, to generate a natural-language summary instead."
        )
        return RecommendResponse(answer=answer, supporting_hospitals=candidates)
