"""POST /recommend — AI Recommendation Assistant."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.services.hospital_service import HospitalService
from app.schemas.hospital import RecommendRequest, RecommendResponse

router = APIRouter(tags=["recommend"])


@router.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest, db: Session = Depends(get_db)):
    service = HospitalService(HospitalRepository(db))
    return service.recommend(
        question=payload.question,
        zip_code=payload.zip_code,
        lat=payload.latitude,
        lon=payload.longitude,
    )
