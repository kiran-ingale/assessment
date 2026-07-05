"""PDF text extraction service."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pdfplumber
from PyPDF2 import PdfReader

from utils.exceptions import EmptyPDFError, InvalidPDFError
from utils.logger import get_logger

logger = get_logger(__name__)

MIN_TEXT_LENGTH = 20


class PDFService:
    """Extract text from PDF files using pdfplumber with PyPDF2 fallback."""

    def extract_text_from_bytes(self, content: bytes, filename: str) -> str:
        """
        Extract text from PDF bytes.

        Raises:
            InvalidPDFError: If the file is not a valid PDF.
            EmptyPDFError: If no meaningful text could be extracted.
        """
        if not content.startswith(b"%PDF"):
            raise InvalidPDFError(
                "Uploaded file is not a valid PDF.",
                details={"filename": filename},
            )

        text = self._extract_with_pdfplumber(content)
        if len(text.strip()) < MIN_TEXT_LENGTH:
            logger.warning("pdfplumber returned little text for %s; trying PyPDF2.", filename)
            text = self._extract_with_pypdf2(content)

        cleaned = self._normalize_text(text)
        if len(cleaned) < MIN_TEXT_LENGTH:
            raise EmptyPDFError(
                "Unable to extract text from PDF. The document may be scanned, image-only, or empty.",
                details={
                    "filename": filename,
                    "hint": "Use OCR preprocessing for scanned documents before upload.",
                },
            )

        logger.info("Extracted %d characters from %s", len(cleaned), filename)
        return cleaned

    def extract_text_from_path(self, file_path: Path) -> str:
        """Extract text from a PDF file on disk."""
        content = file_path.read_bytes()
        return self.extract_text_from_bytes(content, file_path.name)

    def _extract_with_pdfplumber(self, content: bytes) -> str:
        """Primary extraction strategy using pdfplumber."""
        try:
            chunks: list[str] = []
            with pdfplumber.open(BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    if page_text.strip():
                        chunks.append(page_text)
            return "\n\n".join(chunks)
        except Exception as exc:
            logger.exception("pdfplumber extraction failed: %s", exc)
            return ""

    def _extract_with_pypdf2(self, content: bytes) -> str:
        """Fallback extraction strategy using PyPDF2."""
        try:
            reader = PdfReader(BytesIO(content))
            chunks: list[str] = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    chunks.append(page_text)
            return "\n\n".join(chunks)
        except Exception as exc:
            logger.exception("PyPDF2 extraction failed: %s", exc)
            raise InvalidPDFError(
                "Failed to read PDF content.",
                details={"reason": str(exc)},
            ) from exc

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Collapse excessive whitespace while preserving paragraph breaks."""
        lines = [line.strip() for line in text.splitlines()]
        normalized_lines = [line for line in lines if line]
        return "\n".join(normalized_lines)
