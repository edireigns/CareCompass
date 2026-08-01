"""
Core ORM models.

These map directly to the normalized schema described in the project
spec: hospitals, hospital_quality, hospital_outcomes, patient_experience,
insurance, specialties, locations, wait_time_estimates, dataset_metadata.

Kept in one file for scaffold readability; in a larger codebase these
would likely be split one-model-per-file under models/.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


def _uuid():
    return str(uuid.uuid4())


# Many-to-many: hospitals <-> specialties
hospital_specialties = Table(
    "hospital_specialties",
    Base.metadata,
    Column("hospital_id", UUID(as_uuid=False), ForeignKey("hospitals.id"), primary_key=True),
    Column("specialty_id", UUID(as_uuid=False), ForeignKey("specialties.id"), primary_key=True),
)

# Many-to-many: hospitals <-> insurance
hospital_insurance = Table(
    "hospital_insurance",
    Base.metadata,
    Column("hospital_id", UUID(as_uuid=False), ForeignKey("hospitals.id"), primary_key=True),
    Column("insurance_id", UUID(as_uuid=False), ForeignKey("insurance.id"), primary_key=True),
)


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    cms_provider_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False, index=True)
    hospital_type = Column(String, nullable=True)  # e.g. Acute Care, Critical Access
    ownership_type = Column(String, nullable=True)
    emergency_services = Column(Boolean, default=False)
    trauma_level = Column(String, nullable=True)
    teaching_hospital = Column(Boolean, default=False)
    pediatric_hospital = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    location = relationship("Location", back_populates="hospital", uselist=False)
    quality = relationship("HospitalQuality", back_populates="hospital", uselist=False)
    outcomes = relationship("HospitalOutcomes", back_populates="hospital", uselist=False)
    experience = relationship("PatientExperience", back_populates="hospital", uselist=False)
    wait_time = relationship("WaitTimeEstimate", back_populates="hospital", uselist=False)
    specialties = relationship("Specialty", secondary=hospital_specialties, back_populates="hospitals")
    insurance_plans = relationship("Insurance", secondary=hospital_insurance, back_populates="hospitals")


class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    hospital_id = Column(UUID(as_uuid=False), ForeignKey("hospitals.id"), unique=True, nullable=False)
    address_line1 = Column(String, nullable=True)
    city = Column(String, nullable=True, index=True)
    state = Column(String, nullable=True, index=True)
    zip_code = Column(String, nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    hospital = relationship("Hospital", back_populates="location")


class HospitalQuality(Base):
    __tablename__ = "hospital_quality"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)

    hospital_id = Column(
        UUID(as_uuid=False),
        ForeignKey("hospitals.id"),
        unique=True,
        nullable=False,
    )

    cms_overall_rating = Column(Integer, nullable=True)
    quality_of_care_rating = Column(Integer, nullable=True)
    safety_rating = Column(Integer, nullable=True)

    # Mortality
    mortality_group_measure_count = Column(Integer, nullable=True)
    mortality_facility_measure_count = Column(Integer, nullable=True)
    mortality_better = Column(Integer, nullable=True)
    mortality_no_different = Column(Integer, nullable=True)
    mortality_worse = Column(Integer, nullable=True)

    # Safety
    safety_group_measure_count = Column(Integer, nullable=True)
    safety_facility_measure_count = Column(Integer, nullable=True)
    safety_better = Column(Integer, nullable=True)
    safety_no_different = Column(Integer, nullable=True)
    safety_worse = Column(Integer, nullable=True)

    # Readmission
    readmission_group_measure_count = Column(Integer, nullable=True)
    readmission_facility_measure_count = Column(Integer, nullable=True)
    readmission_better = Column(Integer, nullable=True)
    readmission_no_different = Column(Integer, nullable=True)
    readmission_worse = Column(Integer, nullable=True)

    hospital = relationship(
    "Hospital",
    back_populates="quality"
    )


class HospitalOutcomes(Base):
    __tablename__ = "hospital_outcomes"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    hospital_id = Column(UUID(as_uuid=False), ForeignKey("hospitals.id"), unique=True, nullable=False)
    readmission_rate = Column(Float, nullable=True)   # % (national avg ~= baseline)
    mortality_rate = Column(Float, nullable=True)      # %
    infection_rate = Column(Float, nullable=True)      # per 1000 patient-days
    complication_rate = Column(Float, nullable=True)   # %

    hospital = relationship("Hospital", back_populates="outcomes")


class PatientExperience(Base):
    __tablename__ = "patient_experience"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    hospital_id = Column(UUID(as_uuid=False), ForeignKey("hospitals.id"), unique=True, nullable=False)
    overall_satisfaction = Column(Float, nullable=True)     # % patients rating 9-10
    would_recommend_pct = Column(Float, nullable=True)
    communication_score = Column(Float, nullable=True)
    cleanliness_score = Column(Float, nullable=True)

    hospital = relationship("Hospital", back_populates="experience")


class WaitTimeEstimate(Base):
    """Prototype-only estimates, per the spec. Replace with a real feed later."""
    __tablename__ = "wait_time_estimates"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    hospital_id = Column(UUID(as_uuid=False), ForeignKey("hospitals.id"), unique=True, nullable=False)
    er_wait_minutes = Column(Integer, nullable=True)
    appointment_wait_days = Column(Integer, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    hospital = relationship("Hospital", back_populates="wait_time")


class Specialty(Base):
    __tablename__ = "specialties"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name = Column(String, unique=True, nullable=False)

    hospitals = relationship("Hospital", secondary=hospital_specialties, back_populates="specialties")


class Insurance(Base):
    __tablename__ = "insurance"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    name = Column(String, unique=True, nullable=False)

    hospitals = relationship("Hospital", secondary=hospital_insurance, back_populates="insurance_plans")


class DatasetMetadata(Base):
    """Tracks provenance + freshness of each ingested public dataset."""
    __tablename__ = "dataset_metadata"

    id = Column(UUID(as_uuid=False), primary_key=True, default=_uuid)
    source_name = Column(String, nullable=False)   # e.g. "CMS Hospital General Information"
    source_url = Column(String, nullable=True)
    last_fetched_at = Column(DateTime, nullable=True)
    row_count = Column(Integer, nullable=True)
    status = Column(String, default="pending")  # pending | success | failed
