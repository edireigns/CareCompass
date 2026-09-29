from app.api.ranking_context import RankingContext, ranking_context
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
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_miles: float = Query(25, gt=0, le=200),
    context: RankingContext = Depends(ranking_context),
    db: Session = Depends(get_db),
):
    service = HospitalService(HospitalRepository(db))
    return service.nearby(lat, lon, radius_miles=radius_miles, weights=context.weights)
