"""OpenAI-powered document analysis service."""

from __future__ import annotations

import json

from openai import OpenAI
from pydantic import ValidationError

from utils.config import Settings
from utils.exceptions import AIServiceError
from utils.helpers import extract_json_from_text
from utils.logger import get_logger
from utils.models import DocumentAnalysis

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a professional document analyst.
Analyze the provided document text and return ONLY valid JSON with this exact schema:
{
  "summary": "A concise summary between 150 and 250 words.",
  "key_points": ["bullet point 1", "bullet point 2"],
  "action_items": ["actionable task 1", "actionable task 2"],
  "deadlines": ["deadline or date mentioned, if any"],
  "important_entities": ["names, organizations, and important dates"]
}

Rules:
- summary must be 150-250 words
- key_points must be concise bullet-style strings
- action_items must be actionable tasks
- deadlines should be empty array if none are found
- important_entities should include people, organizations, and notable dates
- Do not include markdown fences or commentary outside JSON
"""

USER_PROMPT_TEMPLATE = """Analyze the following document and respond with JSON only.

Document text:
---
{text}
---
"""


class AIService:
    """Generate structured document insights using the OpenAI API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def analyze_document(self, text: str, filename: str) -> DocumentAnalysis:
        """
        Send document text to the LLM and parse structured output.

        Raises:
            AIServiceError: If the API call fails or JSON parsing/validation fails.
        """
        truncated_text = text[:120_000]
        if len(text) > len(truncated_text):
            logger.warning(
                "Document %s truncated from %d to %d characters for LLM input.",
                filename,
                len(text),
                len(truncated_text),
            )

        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": USER_PROMPT_TEMPLATE.format(text=truncated_text),
                    },
                ],
            )
        except Exception as exc:
            logger.exception("OpenAI API request failed for %s", filename)
            raise AIServiceError(
                "Failed to analyze document with OpenAI.",
                details={"reason": str(exc)},
            ) from exc

        raw_content = response.choices[0].message.content or ""
        if not raw_content.strip():
            raise AIServiceError(
                "OpenAI returned an empty response.",
                details={"filename": filename},
            )

        try:
            payload = extract_json_from_text(raw_content)
            analysis = DocumentAnalysis.model_validate(payload)
        except (ValueError, json.JSONDecodeError, ValidationError) as exc:
            logger.exception("Failed to parse OpenAI JSON for %s", filename)
            raise AIServiceError(
                "Failed to parse structured response from OpenAI.",
                details={"reason": str(exc), "raw_response": raw_content[:500]},
            ) from exc

        logger.info("Successfully analyzed document: %s", filename)
        return analysis
