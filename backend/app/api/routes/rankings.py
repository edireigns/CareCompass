"""GET /rankings — top hospitals overall, with customizable weights."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import HospitalSummary, RankingWeights

router = APIRouter(tags=["rankings"])


@router.get("/rankings", response_model=list[HospitalSummary])
def rankings(
    limit: int = 10,
    quality: float = 0.35,
    wait_time: float = 0.25,
    distance: float = 0.20,
    satisfaction: float = 0.10,
    readmission: float = 0.10,
    db: Session = Depends(get_db),
):
    weights = RankingWeights(
        quality=quality, wait_time=wait_time, distance=distance,
        satisfaction=satisfaction, readmission=readmission,
    )
    service = HospitalService(HospitalRepository(db))
    return service.rankings(limit=limit, weights=weights)
