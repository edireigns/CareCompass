from app.api.ranking_context import RankingContext, ranking_context
"""GET /compare — side-by-side comparison of 2-5 hospitals."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import HospitalDetail

router = APIRouter(tags=["compare"])


@router.get("/compare", response_model=list[HospitalDetail])
def compare_hospitals(
    ids: list[str] = Query(..., min_length=2, max_length=5, alias="ids"),
    context: RankingContext = Depends(ranking_context),
    db: Session = Depends(get_db),
):
    service = HospitalService(HospitalRepository(db))
    return service.compare(ids, weights=context.weights, user_lat=context.lat, user_lon=context.lon)
