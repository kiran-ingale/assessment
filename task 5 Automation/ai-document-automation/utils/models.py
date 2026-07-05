"""Shared Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field


class DocumentAnalysis(BaseModel):
    """Structured output from the LLM document analysis."""

    summary: str = Field(..., description="Concise summary between 150-250 words.")
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    important_entities: list[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """JSON response returned by the upload endpoint."""

    success: bool
    filename: str
    summary: str
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    deadlines: list[str] = Field(default_factory=list)
    important_entities: list[str] = Field(default_factory=list)
    sheet_updated: bool
    email_sent: bool


class ErrorResponse(BaseModel):
    """Standard error response payload."""

    success: bool = False
    error: str
    details: str | dict | list | None = None
