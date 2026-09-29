import json
from typing import Any

from openai import AsyncOpenAI

from app.core.config import get_settings


class AIUnavailableError(RuntimeError):
    """The optional AI assistant has not been configured for this service."""


AI_INSTRUCTIONS = """
You are the CareCompass hospital data assistant.

Rules:
- Base answers only on the CMS hospital data provided in the request.
- Never invent hospital ratings, outcomes, services, distances, or statistics.
- Clearly say when the provided data is insufficient.
- Explain comparisons in simple, neutral language.
- Do not diagnose medical conditions or recommend medical treatment.
- Do not claim that a hospital is medically best for a specific patient.
- For emergencies, remind the user to call 911 or local emergency services.
- Mention which CMS measurements support the answer.
"""


class AIService:
    def __init__(self) -> None:
        settings = get_settings()

        self.client = (
            AsyncOpenAI(api_key=settings.openai_api_key)
            if settings.openai_api_key else None
        )
        self.model = settings.openai_model

    async def answer_question(
        self,
        question: str,
        hospital_data: dict[str, Any] | list[dict[str, Any]],
    ) -> str:
        if self.client is None:
            raise AIUnavailableError("The AI assistant is not configured for this preview.")

        cms_context = json.dumps(
            hospital_data,
            indent=2,
            default=str,
        )

        response = await self.client.responses.create(
            model=self.model,
            instructions=AI_INSTRUCTIONS,
            input=(
                f"User question:\n{question}\n\n"
                f"Available CMS hospital data:\n{cms_context}"
            ),
        )

        answer = response.output_text.strip()

        if not answer:
            return "I could not generate an answer from the available CMS data."

        return answer


ai_service = AIService()
