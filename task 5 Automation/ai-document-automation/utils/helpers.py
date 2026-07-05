"""Utility helpers."""

from __future__ import annotations

import json
import re
from typing import Any


def join_list_for_sheet(items: list[str]) -> str:
    """Join list items into a single cell-friendly string."""
    return " | ".join(item.strip() for item in items if item.strip())


def extract_json_from_text(text: str) -> dict[str, Any]:
    """
    Extract and parse a JSON object from LLM output.

    Handles fenced code blocks and stray text around the JSON payload.
    """
    cleaned = text.strip()

    fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if fenced_match:
        cleaned = fenced_match.group(1)

    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in LLM response.")
        cleaned = cleaned[start : end + 1]

    return json.loads(cleaned)


def sanitize_filename(filename: str) -> str:
    """Remove unsafe characters from uploaded filenames."""
    base_name = filename.replace("\\", "/").split("/")[-1]
    safe = re.sub(r"[^\w.\- ]", "_", base_name).strip()
    return safe or "upload.pdf"
