"""POST /recommend — AI Recommendation Assistant."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.schemas.hospital import RecommendRequest, RecommendResponse
from app.services.hospital_service import HospitalService


router = APIRouter(tags=["recommend"])
logger = logging.getLogger("carecompass.ai")


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(
    payload: RecommendRequest,
    db: Session = Depends(get_db),
) -> RecommendResponse:
    service = HospitalService(HospitalRepository(db))

    try:
        return await service.recommend(
            question=payload.question,
            city=payload.city,
            state=payload.state,
            zip_code=payload.zip_code,
            lat=payload.latitude,
            lon=payload.longitude,
        )
    except OpenAIError:
        logger.exception("OpenAI request failed")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI assistant is temporarily unavailable.",
        )