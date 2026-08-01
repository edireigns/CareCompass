"""Shared FastAPI dependencies."""
from typing import Generator
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_hospital_service(db: Session = None) -> HospitalService:
    """Convenience factory; routes typically call this via Depends chain below."""
    return HospitalService(HospitalRepository(db))
