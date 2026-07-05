"""FastAPI application for AI-powered PDF document automation."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from services.ai_service import AIService
from services.email_service import EmailService
from services.pdf_service import PDFService
from services.sheets_service import SheetsService
from utils.config import get_settings
from utils.exceptions import AppError, ConfigurationError
from utils.logger import get_logger, setup_logging
from utils.models import ErrorResponse, UploadResponse
from utils.helpers import sanitize_filename

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="AI Document Automation API",
    description=(
        "Upload a PDF to extract text, generate AI insights, "
        "store results in Google Sheets, and email a summary."
    ),
    version="1.0.0",
)

try:
    settings = get_settings()
except ValidationError as exc:
    logger.error("Missing or invalid environment configuration: %s", exc)
    settings = None


def _get_services() -> tuple[PDFService, AIService, SheetsService, EmailService]:
    """Instantiate service layer with validated settings."""
    if settings is None:
        raise ConfigurationError(
            "Application is not configured. Copy .env.example to .env and provide all required values.",
            details={"validation_errors": "See server logs for missing environment variables."},
        )
    return (
        PDFService(),
        AIService(settings),
        SheetsService(settings),
        EmailService(settings),
    )


@app.get("/")
async def root() -> dict[str, str]:
    """Health and discovery endpoint."""
    return {
        "service": "AI Document Automation API",
        "status": "running",
        "upload_endpoint": "POST /upload",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check endpoint."""
    configured = settings is not None
    return {
        "status": "healthy" if configured else "misconfigured",
        "configuration_loaded": str(configured).lower(),
    }


@app.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
)
async def upload_pdf(
    file: UploadFile = File(..., description="PDF file to analyze"),
) -> UploadResponse:
    """
    Upload a PDF, analyze it with AI, store results in Google Sheets, and email a summary.

    Returns structured analysis data along with integration status flags.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    safe_filename = sanitize_filename(file.filename)
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if settings is not None and len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum upload size of {settings.max_upload_size_mb} MB.",
        )

    pdf_service, ai_service, sheets_service, email_service = _get_services()

    saved_path: Path | None = None
    sheet_updated = False
    email_sent = False

    try:
        extracted_text = pdf_service.extract_text_from_bytes(content, safe_filename)

        if settings is not None:
            unique_name = f"{uuid.uuid4().hex}_{safe_filename}"
            saved_path = settings.uploads_dir / unique_name
            saved_path.write_bytes(content)
            logger.info("Saved uploaded PDF to %s", saved_path)

        analysis = ai_service.analyze_document(extracted_text, safe_filename)

        try:
            sheets_service.append_analysis(safe_filename, analysis)
            sheet_updated = True
        except AppError as exc:
            logger.error("Google Sheets update failed: %s", exc.message)

        try:
            email_service.send_summary_email(safe_filename, analysis)
            email_sent = True
        except AppError as exc:
            logger.error("Email delivery failed: %s", exc.message)

        return UploadResponse(
            success=True,
            filename=safe_filename,
            summary=analysis.summary,
            key_points=analysis.key_points,
            action_items=analysis.action_items,
            deadlines=analysis.deadlines,
            important_entities=analysis.important_entities,
            sheet_updated=sheet_updated,
            email_sent=email_sent,
        )
    except AppError as exc:
        logger.error("Request failed: %s", exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(error=exc.message, details=exc.details).model_dump(),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while processing upload.")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="An unexpected error occurred while processing the document.",
                details={"reason": str(exc)},
            ).model_dump(),
        )


@app.exception_handler(ConfigurationError)
async def configuration_error_handler(_request, exc: ConfigurationError) -> JSONResponse:
    """Return a clear response when environment configuration is invalid."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.message, details=exc.details).model_dump(),
    )
