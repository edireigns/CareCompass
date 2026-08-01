"""GET /nearby — hospitals within a radius of a lat/lon point."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import HospitalSummary

router = APIRouter(tags=["nearby"])


@router.get("/nearby", response_model=list[HospitalSummary])
def nearby_hospitals(
    lat: float,
    lon: float,
    radius_miles: float = Query(25, le=200),
    db: Session = Depends(get_db),
):
    service = HospitalService(HospitalRepository(db))
    return service.nearby(lat, lon, radius_miles=radius_miles)
