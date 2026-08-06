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
from app.services.ai_service import ai_service

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
        self, city=None, state=None, zip_code=None, specialty=None, emergency_only=False,
        trauma_level=None, teaching_only=False, pediatric_only=False,
        user_lat=None, user_lon=None, weights: Optional[RankingWeights] = None,
    ) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        hospitals = self.repo.search(
            city=city, state=state, zip_code=zip_code, specialty=specialty,
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
        hospitals = self.repo.list_all(limit=10_000) # over-fetch, then sort + trim
        results = [self._to_summary(h, weights) for h in hospitals]
        return sorted(results, key=lambda h: h.overall_score or 0, reverse=True)[:limit]

    async def recommend(
        self,
        question: str,
        city: Optional[str] = None,
        state: Optional[str] =None,
        zip_code: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> RecommendResponse:
        """
        Select relevant hospitals using CareCompass ranking logic, then ask
        OpenAI to explain the results using only the selected CMS data.
        """
        weights = RankingWeights()

        if lat is not None and lon is not None:
            candidates = self.nearby(
                lat,
                lon,
                radius_miles=25,
                weights=weights,
            )[:5]
        elif city or state or zip_code:
            candidates = self.search(
                city=city.strip() if city else None,
                state=state.strip().upper() if state else None,
                zip_code=zip_code.strip() if zip_code else None,
                weights=weights,
            )[:5]
        else:
            candidates = self.rankings(
                limit=5,
                weights=weights,
            )

        if not candidates:
            return RecommendResponse(
                answer=(
                    "No hospitals matched the provided location or search "
                    "information."
                ),
                supporting_hospitals=[],
            )

        hospital_ids = [hospital.id for hospital in candidates]
        detailed_hospitals = self.compare(hospital_ids, weights)

        cms_context = [
            hospital.model_dump(mode="json")
            for hospital in detailed_hospitals
        ]

        answer = await ai_service.answer_question(
            question=question,
            hospital_data=cms_context,
        )

        return RecommendResponse(
            answer=answer,
            supporting_hospitals=candidates,
        )