"""GET /search — hospital search by city, ZIP, specialty, and filters."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import HospitalSummary

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[HospitalSummary])
def search_hospitals(
    city: Optional[str] = None,
    zip_code: Optional[str] = Query(None, alias="zip"),
    specialty: Optional[str] = None,
    emergency_only: bool = False,
    trauma_level: Optional[str] = None,
    teaching_only: bool = False,
    pediatric_only: bool = False,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    db: Session = Depends(get_db),
):
    service = HospitalService(HospitalRepository(db))
    return service.search(
        city=city, zip_code=zip_code, specialty=specialty,
        emergency_only=emergency_only, trauma_level=trauma_level,
        teaching_only=teaching_only, pediatric_only=pediatric_only,
        user_lat=lat, user_lon=lon,
    )
