from pydantic import BaseModel, Field


class AIQuestionRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=1000,
        description="Question about hospitals or CMS quality data",
    )
    facility_ids: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="CMS Facility IDs to include in the answer",
    )


class AIAnswerResponse(BaseModel):
    answer: str
    facility_ids: list[str]
    data_source: str = "CMS Care Compare"