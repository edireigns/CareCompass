"""
Repository layer: the only place in the codebase that writes SQLAlchemy
queries. Services talk to this class, never to the ORM directly, so the
persistence layer can be swapped or optimized without touching business logic.
"""
from typing import Optional
from datetime import date
from sqlalchemy import exists
from sqlalchemy.orm import Session, joinedload, selectinload
from app.models.data import DirectoryEntry

from app.models.hospital import Hospital, Location, Specialty, Insurance, HospitalQuality, HospitalOutcomes, PatientExperience, WaitTimeEstimate


class HospitalRepository:
    def __init__(self, db: Session):
        self.db = db

    def _base_query(self):
        return self.db.query(Hospital).options(
            joinedload(Hospital.location),
            joinedload(Hospital.quality),
            joinedload(Hospital.outcomes),
            joinedload(Hospital.experience),
            joinedload(Hospital.wait_time),
            selectinload(Hospital.specialties),
            selectinload(Hospital.insurance_plans),
        )

    def get_by_id(self, hospital_id: str) -> Optional[Hospital]:
        return self._base_query().filter(Hospital.id == hospital_id).first()

    def get_by_ids(self, hospital_ids: list[str]) -> list[Hospital]:
        return self._base_query().filter(Hospital.id.in_(hospital_ids)).all()

    def search(
        self,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        specialty: Optional[str] = None,
        insurance: Optional[str] = None,
        carrier: Optional[str] = None,
        emergency_only: bool = False,
        trauma_level: Optional[str] = None,
        teaching_only: bool = False,
        pediatric_only: bool = False,
        limit: int = 500,
    ) -> list[Hospital]:
        query = self._base_query().join(Location)

        if city:
            query = query.filter(Location.city.ilike(f"%{city}%"))
        if state:
            query = query.filter(Location.state.ilike(state))
        if zip_code:
            query = query.filter(Location.zip_code == zip_code)
        if specialty:
            from app.services.directory_taxonomy import specialty_names
            names=[r[0] for r in self.db.query(DirectoryEntry.name).filter_by(kind='specialty').distinct()]
            aliases=specialty_names(specialty,names)
            query = query.filter(exists().where(DirectoryEntry.hospital_id == Hospital.id, DirectoryEntry.kind == "specialty", DirectoryEntry.name.in_(aliases), (DirectoryEntry.expires_on.is_(None)) | (DirectoryEntry.expires_on >= date.today().isoformat())))
        if carrier:
            from app.services.directory_taxonomy import insurance_carrier
            names=[name for name in self.list_insurance() if insurance_carrier(name)==carrier]
            query=query.filter(exists().where(DirectoryEntry.hospital_id==Hospital.id,DirectoryEntry.kind=='insurance',DirectoryEntry.name.in_(names),(DirectoryEntry.expires_on.is_(None)) | (DirectoryEntry.expires_on>=date.today().isoformat())))
        if insurance:
            query = query.filter(exists().where(DirectoryEntry.hospital_id == Hospital.id, DirectoryEntry.kind == "insurance", DirectoryEntry.name == insurance, (DirectoryEntry.expires_on.is_(None)) | (DirectoryEntry.expires_on >= date.today().isoformat())))
        if emergency_only:
            query = query.filter(Hospital.emergency_services.is_(True))
        if trauma_level:
            query = query.filter(Hospital.trauma_level == trauma_level)
        if teaching_only:
            query = query.filter(Hospital.teaching_hospital.is_(True))
        if pediatric_only:
            query = query.filter(Hospital.pediatric_hospital.is_(True))

        return query.limit(limit).all()

    def list_all(self, limit: Optional[int] = None) -> list[Hospital]:
        # Ranking only needs score inputs; directory collections belong on
        # detail/search paths and are expensive across the full catalog.
        query = self.db.query(Hospital).options(
            joinedload(Hospital.location),
            joinedload(Hospital.quality),
            joinedload(Hospital.outcomes),
            joinedload(Hospital.experience),
            joinedload(Hospital.wait_time),
        ).order_by(Hospital.id)
        return (query.limit(limit) if limit else query).all()

    def ranking_inputs(self):
        """Read only the seven columns needed to choose ranking winners."""
        return self.db.query(
            Hospital.id.label('id'),
            HospitalQuality.cms_overall_rating.label('rating'),
            WaitTimeEstimate.er_wait_minutes.label('wait_minutes'),
            PatientExperience.overall_satisfaction.label('satisfaction'),
            HospitalOutcomes.readmission_rate.label('readmission'),
            Location.latitude.label('latitude'),
            Location.longitude.label('longitude'),
        ).outerjoin(HospitalQuality, Hospital.id == HospitalQuality.hospital_id).outerjoin(
            WaitTimeEstimate, Hospital.id == WaitTimeEstimate.hospital_id
        ).outerjoin(PatientExperience, Hospital.id == PatientExperience.hospital_id).outerjoin(
            HospitalOutcomes, Hospital.id == HospitalOutcomes.hospital_id
        ).outerjoin(Location, Hospital.id == Location.hospital_id).order_by(Hospital.id).all()

    def nearby_candidates(self, lat: float, radius_miles: float):
        delta = radius_miles / 68.5
        return self._base_query().join(Location).filter(Location.latitude.between(max(-90, lat-delta), min(90, lat+delta)), Location.longitude.isnot(None)).all()

    def list_specialties(self) -> list[str]:
        from app.services.directory_taxonomy import specialty_category
        return sorted({specialty_category(r[0]) for r in self.db.query(DirectoryEntry.name).filter(DirectoryEntry.kind == "specialty", (DirectoryEntry.expires_on.is_(None)) | (DirectoryEntry.expires_on >= date.today().isoformat())).distinct().order_by(DirectoryEntry.name).all()})

    def list_insurance(self) -> list[str]:
        from datetime import date
        from app.models.data import DirectoryEntry
        return [r[0] for r in self.db.query(DirectoryEntry.name).filter(DirectoryEntry.kind == "insurance", (DirectoryEntry.expires_on.is_(None)) | (DirectoryEntry.expires_on >= date.today().isoformat())).distinct().order_by(DirectoryEntry.name).all()]
