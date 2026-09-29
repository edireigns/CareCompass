"""
Pydantic schemas — the shapes that cross the API boundary.

Kept separate from ORM models (app/models) on purpose: the DB shape and
the wire shape are allowed to drift independently as the product grows.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field


class LocationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    address_line1: Optional[str] = None
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

    mortality_group_measure_count: Optional[int] = None
    mortality_facility_measure_count: Optional[int] = None
    mortality_better: Optional[int] = None
    mortality_no_different: Optional[int] = None
    mortality_worse: Optional[int] = None

    safety_group_measure_count: Optional[int] = None
    safety_facility_measure_count: Optional[int] = None
    safety_better: Optional[int] = None
    safety_no_different: Optional[int] = None
    safety_worse: Optional[int] = None

    readmission_group_measure_count: Optional[int] = None
    readmission_facility_measure_count: Optional[int] = None
    readmission_better: Optional[int] = None
    readmission_no_different: Optional[int] = None
    readmission_worse: Optional[int] = None

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


class ScoreComponent(BaseModel):
    key: str
    label: str
    value: Optional[float] = None
    unit: str
    available: bool
    requested_weight: float
    effective_weight: float
    score: Optional[float] = None
    contribution: Optional[float] = None
    formula: str
    date_status: str = 'unknown'
    measure_id: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    release_date: Optional[str] = None
    source_url: Optional[str] = None
    source_note: Optional[str] = None

class ScoreExplanation(BaseModel):
    overall_score: Optional[float] = None
    coverage_pct: float
    sufficient_data: bool
    components: list[ScoreComponent]

class ScoreFreshness(BaseModel):
    summary: str
    older_measure_count: int
    unknown_period_count: int
    oldest_period_end: Optional[str] = None
    newest_period_end: Optional[str] = None

class PresenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    present: bool
    checked_on: str
    release_date: Optional[str] = None

class HospitalSummary(BaseModel):
    """Lightweight shape used in search / list / ranking results."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    cms_presence: Optional[PresenceOut] = None
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
    score_explanation: Optional[ScoreExplanation] = None
    score_freshness: Optional[ScoreFreshness] = None


class MeasureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    measure_id: str
    source_key: str
    name: str
    value: float
    unit: str
    comparison: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    source_url: str

    @computed_field
    @property
    def freshness(self) -> str:
        from app.services.freshness_service import reporting_status
        return reporting_status(self.period_end)

class DirectoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    kind: str
    name: str
    source_url: str
    source_label: str
    verified_on: str
    expires_on: Optional[str] = None

    @computed_field
    @property
    def freshness(self) -> str:
        from app.services.freshness_service import directory_status
        return directory_status(self.verified_on, self.expires_on)

    @computed_field
    @property
    def search_category(self) -> str:
        from app.services.directory_taxonomy import specialty_category, insurance_carrier
        return specialty_category(self.name) if self.kind == 'specialty' else insurance_carrier(self.name)

class HospitalDetail(HospitalSummary):
    """Full shape used on the hospital detail page."""
    cms_provider_id: Optional[str] = None
    ownership_type: Optional[str] = None
    outcomes: Optional[OutcomesOut] = None
    experience: Optional[ExperienceOut] = None
    specialties: list[str] = Field(default_factory=list)
    insurance_plans: list[str] = Field(default_factory=list)
    measures: list[MeasureOut] = Field(default_factory=list)
    directory_entries: list[DirectoryOut] = Field(default_factory=list)

    @field_validator('specialties', 'insurance_plans', mode='before')
    @classmethod
    def names(cls, value):
        return [getattr(item, 'name', item) for item in (value or [])]


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
