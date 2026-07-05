from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9_.-]+")


def sanitize_filename(name: str) -> str:
    """Return a conservative filename that is safe to store inside uploads/."""
    cleaned = SAFE_FILENAME_RE.sub("_", Path(name).name).strip("._")
    return cleaned or "uploaded_document"


def mask_secret(value: Optional[str]) -> str:
    if not value:
        return "not set"
    if len(value) <= 8:
        return "set"
    return f"{value[:4]}...{value[-4:]}"
