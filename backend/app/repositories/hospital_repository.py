"""
Repository layer: the only place in the codebase that writes SQLAlchemy
queries. Services talk to this class, never to the ORM directly, so the
persistence layer can be swapped or optimized without touching business logic.
"""
from typing import Optional
from sqlalchemy.orm import Session, joinedload

from app.models.hospital import Hospital, Location, Specialty, Insurance


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
            joinedload(Hospital.specialties),
            joinedload(Hospital.insurance_plans),
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
        emergency_only: bool = False,
        trauma_level: Optional[str] = None,
        teaching_only: bool = False,
        pediatric_only: bool = False,
        limit: int = 25,
    ) -> list[Hospital]:
        query = self._base_query().join(Location)

        if city:
            query = query.filter(Location.city.ilike(f"%{city}%"))
        if state:
            query = query.filter(Location.state.ilike(state))
        if zip_code:
            query = query.filter(Location.zip_code == zip_code)
        if specialty:
            query = query.join(Hospital.specialties).filter(Specialty.name.ilike(f"%{specialty}%"))
        if emergency_only:
            query = query.filter(Hospital.emergency_services.is_(True))
        if trauma_level:
            query = query.filter(Hospital.trauma_level == trauma_level)
        if teaching_only:
            query = query.filter(Hospital.teaching_hospital.is_(True))
        if pediatric_only:
            query = query.filter(Hospital.pediatric_hospital.is_(True))

        return query.limit(limit).all()

    def list_all(self, limit: int = 100) -> list[Hospital]:
        return self._base_query().limit(limit).all()

    def list_specialties(self) -> list[str]:
        return [s.name for s in self.db.query(Specialty).all()]

    def list_insurance(self) -> list[str]:
        return [i.name for i in self.db.query(Insurance).all()]
