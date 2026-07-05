"""Custom application exceptions with HTTP status codes."""

from typing import Any


class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 500, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class ConfigurationError(AppError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=500, details=details)


class InvalidPDFError(AppError):
    """Raised when an uploaded file is not a valid PDF."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=400, details=details)


class EmptyPDFError(AppError):
    """Raised when a PDF contains no extractable text."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=422, details=details)


class AIServiceError(AppError):
    """Raised when OpenAI processing fails."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=502, details=details)


class SheetsServiceError(AppError):
    """Raised when Google Sheets update fails."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=502, details=details)


class EmailServiceError(AppError):
    """Raised when email delivery fails."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message, status_code=502, details=details)
