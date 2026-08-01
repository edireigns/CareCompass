"""GET /specialties — list of all specialties available for filtering."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository

router = APIRouter(tags=["specialties"])


@router.get("/specialties", response_model=list[str])
def list_specialties(db: Session = Depends(get_db)):
    return HospitalRepository(db).list_specialties()
