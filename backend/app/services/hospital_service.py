"""
Service layer: orchestrates repositories + business logic (distance
calculation, ranking, comparison, and the AI assistant's grounding step).
Routes call services; services call repositories. Routes never touch
the ORM or the DB session directly.
"""
from typing import Optional
from types import SimpleNamespace
from geopy.distance import geodesic

from app.models.hospital import Hospital
from app.repositories.hospital_repository import HospitalRepository
from app.schemas.hospital import (
    HospitalSummary, HospitalDetail, RankingWeights, RecommendResponse,
)
from app.services.ranking_service import compute_overall_score, explain_score, ranking_key
from app.schemas.hospital import ScoreExplanation
from app.services.ai_service import ai_service

class HospitalService:
    def __init__(self, repo: HospitalRepository):
        self.repo = repo
        self._score_evidence = {}

    def _load_score_evidence(self, hospitals):
        from app.models.data import HospitalMeasure
        from app.services.score_dates import MEASURE_IDS
        db=getattr(self.repo,'db',None)
        self._score_evidence={}
        if db is None or not hospitals: return
        ids=[h.id for h in hospitals]
        measures=db.query(HospitalMeasure).filter(HospitalMeasure.hospital_id.in_(ids),HospitalMeasure.measure_id.in_([mid for mids in MEASURE_IDS.values() for mid in mids])).all()
        for measure in measures: self._score_evidence.setdefault(measure.hospital_id,[]).append(measure)

    def _score_dates(self, result):
        from app.schemas.hospital import ScoreFreshness
        from app.services.score_dates import attach_score_dates
        result.score_freshness=ScoreFreshness(**attach_score_dates(result.score_explanation,self._score_evidence.get(result.id,[]),result.cms_presence))

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
        summary.score_explanation = ScoreExplanation(**explain_score(hospital, weights, distance))
        summary.overall_score = summary.score_explanation.overall_score
        self._score_dates(summary)
        return summary

    def search(
        self, city=None, state=None, zip_code=None, specialty=None, insurance=None, carrier=None, emergency_only=False,
        trauma_level=None, teaching_only=False, pediatric_only=False,
        user_lat=None, user_lon=None, weights: Optional[RankingWeights] = None,
    ) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        hospitals = self.repo.search(
            city=city, state=state, zip_code=zip_code, specialty=specialty, insurance=insurance, carrier=carrier,
            emergency_only=emergency_only, trauma_level=trauma_level,
            teaching_only=teaching_only, pediatric_only=pediatric_only,
        )
        self._load_score_evidence(hospitals)
        results = [self._to_summary(h, weights, user_lat, user_lon) for h in hospitals]
        return sorted(results, key=ranking_key, reverse=True)

    def nearby(self, lat: float, lon: float, radius_miles: float = 25, weights: Optional[RankingWeights] = None) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        all_hospitals = self.repo.nearby_candidates(lat, radius_miles)
        self._load_score_evidence(all_hospitals)
        results = []
        for h in all_hospitals:
            distance = self._distance_miles(h, lat, lon)
            if distance is not None and distance <= radius_miles:
                summary = self._to_summary(h, weights, lat, lon)
                results.append(summary)
        return sorted(results, key=lambda h: h.distance_miles if h.distance_miles is not None else 9999)

    def get_detail(self, hospital_id: str, weights: Optional[RankingWeights] = None, user_lat=None, user_lon=None) -> Optional[HospitalDetail]:
        weights = weights or RankingWeights()
        hospital = self.repo.get_by_id(hospital_id)
        if not hospital:
            return None
        self._load_score_evidence([hospital])
        distance = self._distance_miles(hospital, user_lat, user_lon)
        detail = HospitalDetail.model_validate(hospital)
        detail.distance_miles = distance
        detail.score_explanation = ScoreExplanation(**explain_score(hospital, weights, distance))
        detail.overall_score = detail.score_explanation.overall_score
        self._score_dates(detail)
        detail.specialties = [s.name for s in hospital.specialties]
        detail.insurance_plans = [i.name for i in hospital.insurance_plans]
        self._enrich_detail(detail, hospital.id)
        return detail

    def compare(self, hospital_ids: list[str], weights: Optional[RankingWeights] = None, user_lat=None, user_lon=None) -> list[HospitalDetail]:
        weights = weights or RankingWeights()
        hospitals = self.repo.get_by_ids(hospital_ids)
        self._load_score_evidence(hospitals)
        details = []
        for h in hospitals:
            detail = HospitalDetail.model_validate(h)
            detail.distance_miles = self._distance_miles(h, user_lat, user_lon)
            detail.score_explanation = ScoreExplanation(**explain_score(h, weights, detail.distance_miles))
            detail.overall_score = detail.score_explanation.overall_score
            self._score_dates(detail)
            detail.specialties = [s.name for s in h.specialties]
            detail.insurance_plans = [i.name for i in h.insurance_plans]
            self._enrich_detail(detail, h.id)
            details.append(detail)
        return sorted(details, key=lambda d: hospital_ids.index(d.id))

    def rankings(self, limit: int = 10, weights: Optional[RankingWeights] = None, user_lat=None, user_lon=None) -> list[HospitalSummary]:
        weights = weights or RankingWeights()
        # Select compact score inputs for the entire catalog, then load full
        # hospital records and measure provenance for only the winners.
        ranked=[]
        for row in self.repo.ranking_inputs():
            candidate=SimpleNamespace(
                location=SimpleNamespace(latitude=row.latitude,longitude=row.longitude),
                quality=SimpleNamespace(cms_overall_rating=row.rating),
                wait_time=SimpleNamespace(er_wait_minutes=row.wait_minutes),
                experience=SimpleNamespace(overall_satisfaction=row.satisfaction),
                outcomes=SimpleNamespace(readmission_rate=row.readmission),
            )
            distance=self._distance_miles(candidate,user_lat,user_lon)
            explanation=explain_score(candidate,weights,distance)
            ranked.append((row.id,explanation))
        ranked.sort(key=lambda item:(item[1]['sufficient_data'],item[1]['overall_score'] if item[1]['overall_score'] is not None else -1),reverse=True)
        selected_ids=[hospital_id for hospital_id,_ in ranked[:limit]]
        by_id={hospital.id:hospital for hospital in self.repo.get_by_ids(selected_ids)}
        selected=[by_id[hospital_id] for hospital_id in selected_ids]
        self._load_score_evidence(selected)
        return [self._to_summary(h,weights,user_lat,user_lon) for h in selected]

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
    def _enrich_detail(self, detail, hospital_id):
        from datetime import date
        from app.models.data import HospitalMeasure, DirectoryEntry
        from app.schemas.hospital import MeasureOut, DirectoryOut
        db = getattr(self.repo, "db", None)
        if db is None: return
        detail.measures = [MeasureOut.model_validate(m) for m in db.query(HospitalMeasure).filter_by(hospital_id=hospital_id).order_by(HospitalMeasure.source_key, HospitalMeasure.measure_id).all()]
        detail.directory_entries = [DirectoryOut.model_validate(e) for e in db.query(DirectoryEntry).filter_by(hospital_id=hospital_id).order_by(DirectoryEntry.kind, DirectoryEntry.name).all()]
        active = [e for e in detail.directory_entries if not e.expires_on or e.expires_on >= date.today().isoformat()]
        detail.insurance_plans = [e.name for e in active if e.kind == "insurance"]
        detail.specialties = [e.name for e in active if e.kind == "specialty"]
