"""
Pydantic schemas — the shapes that cross the API boundary.

Kept separate from ORM models (app/models) on purpose: the DB shape and
the wire shape are allowed to drift independently as the product grows.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class QualityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    cms_overall_rating: Optional[int] = None
    quality_of_care_rating: Optional[int] = None
    safety_rating: Optional[int] = None


class OutcomesOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    readmission_rate: Optional[float] = None
    mortality_rate: Optional[float] = None
    infection_rate: Optional[float] = None
    complication_rate: Optional[float] = None


class ExperienceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    overall_satisfaction: Optional[float] = None
    would_recommend_pct: Optional[float] = None
    communication_score: Optional[float] = None
    cleanliness_score: Optional[float] = None


class WaitTimeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    er_wait_minutes: Optional[int] = None
    appointment_wait_days: Optional[int] = None


class HospitalSummary(BaseModel):
    """Lightweight shape used in search / list / ranking results."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    hospital_type: Optional[str] = None
    emergency_services: bool = False
    trauma_level: Optional[str] = None
    teaching_hospital: bool = False
    pediatric_hospital: bool = False
    location: Optional[LocationOut] = None
    quality: Optional[QualityOut] = None
    wait_time: Optional[WaitTimeOut] = None
    distance_miles: Optional[float] = None
    overall_score: Optional[float] = None


class HospitalDetail(HospitalSummary):
    """Full shape used on the hospital detail page."""
    outcomes: Optional[OutcomesOut] = None
    experience: Optional[ExperienceOut] = None
    specialties: list[str] = Field(default_factory=list)
    insurance_plans: list[str] = Field(default_factory=list)


class RankingWeights(BaseModel):
    """User-customizable weights for the smart ranking algorithm.

    Defaults match the spec (35/25/20/10/10) and are validated to sum to 1.0
    by the ranking service, not here, so partial weight updates are easy.
    """
    quality: float = 0.35
    wait_time: float = 0.25
    distance: float = 0.20
    satisfaction: float = 0.10
    readmission: float = 0.10


class CompareRequest(BaseModel):
    hospital_ids: list[str] = Field(min_length=2, max_length=5)


class RecommendRequest(BaseModel):
    question: str = Field(min_length=3,  max_length=1000)
    city: Optional[str] = None
    state: Optional[str] = Field(default=None, min_length=2, max_length=2)
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RecommendResponse(BaseModel):
    answer: str
    supporting_hospitals: list[HospitalSummary] = Field(default_factory=list)
    disclaimer: str = (
        "This is informational only, based on public quality and outcomes "
        "data, and is not medical advice. In an emergency, call 911."
    )
