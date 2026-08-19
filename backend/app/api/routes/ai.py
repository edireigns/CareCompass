from fastapi import APIRouter, Depends, HTTPException, status
from openai import OpenAIError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.hospital_repository import HospitalRepository
from app.schemas.ai import AIAnswerResponse, AIQuestionRequest
from app.services.ai_service import ai_service


router = APIRouter(prefix="/ai", tags=["AI Assistant"])


def hospital_to_ai_context(hospital) -> dict:
    """Convert a hospital ORM object into safe CMS context for the AI."""

    return {
        "facility_id": hospital.id,
        "name": hospital.name,
        "hospital_type": hospital.hospital_type,
        "emergency_services": hospital.emergency_services,
        "trauma_level": hospital.trauma_level,
        "teaching_hospital": hospital.teaching_hospital,
        "pediatric_hospital": hospital.pediatric_hospital,
        "location": {
            "city": hospital.location.city,
            "state": hospital.location.state,
            "zip_code": hospital.location.zip_code,
        }
        if hospital.location
        else None,
        "quality": {
            "cms_overall_rating": hospital.quality.cms_overall_rating,
            "quality_of_care_rating": hospital.quality.quality_of_care_rating,
            "safety_rating": hospital.quality.safety_rating,
        }
        if hospital.quality
        else None,
        "outcomes": {
            "readmission_rate": hospital.outcomes.readmission_rate,
            "mortality_rate": hospital.outcomes.mortality_rate,
            "infection_rate": hospital.outcomes.infection_rate,
            "complication_rate": hospital.outcomes.complication_rate,
        }
        if hospital.outcomes
        else None,
        "patient_experience": {
            "overall_satisfaction": hospital.experience.overall_satisfaction,
            "would_recommend_pct": hospital.experience.would_recommend_pct,
            "communication_score": hospital.experience.communication_score,
            "cleanliness_score": hospital.experience.cleanliness_score,
        }
        if hospital.experience
        else None,
        "wait_time": {
            "er_wait_minutes": hospital.wait_time.er_wait_minutes,
            "appointment_wait_days": hospital.wait_time.appointment_wait_days,
        }
        if hospital.wait_time
        else None,
        "specialties": [
            specialty.name for specialty in hospital.specialties
        ],
    }


@router.post(
    "/ask",
    response_model=AIAnswerResponse,
    status_code=status.HTTP_200_OK,
)
async def ask_ai(
    request: AIQuestionRequest,
    db: Session = Depends(get_db),
) -> AIAnswerResponse:
    if not request.facility_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select at least one hospital.",
        )

    repository = HospitalRepository(db)
    hospitals = repository.get_by_ids(request.facility_ids)

    if not hospitals:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hospitals were found for the provided Facility IDs.",
        )

    hospital_context = [
        hospital_to_ai_context(hospital) for hospital in hospitals
    ]

    try:
        answer = await ai_service.answer_question(
            question=request.question,
            hospital_data=hospital_context,
        )
    except OpenAIError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI service is temporarily unavailable.",
        )

    found_ids = [hospital.id for hospital in hospitals]

    return AIAnswerResponse(
        answer=answer,
        facility_ids=found_ids,
    )