"""GET /hospital/{id} — full detail page data for one hospital."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import HospitalDetail

router = APIRouter(tags=["hospital"])


@router.get("/hospital/{hospital_id}", response_model=HospitalDetail)
def get_hospital(
    hospital_id: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
    db: Session = Depends(get_db),
):
    service = HospitalService(HospitalRepository(db))
    detail = service.get_detail(hospital_id, user_lat=lat, user_lon=lon)
    if not detail:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return detail
