"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Validated application settings sourced from `.env` and environment."""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    google_sheet_name: str = Field(..., alias="GOOGLE_SHEET_NAME")
    google_service_account_json: str = Field(..., alias="GOOGLE_SERVICE_ACCOUNT_JSON")

    smtp_host: str = Field(..., alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(..., alias="SMTP_USER")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    sender_email: str = Field(..., alias="SENDER_EMAIL")
    receiver_email: str = Field(..., alias="RECEIVER_EMAIL")

    max_upload_size_mb: int = Field(default=10, alias="MAX_UPLOAD_SIZE_MB")

    @field_validator("google_service_account_json")
    @classmethod
    def resolve_credentials_path(cls, value: str) -> str:
        """Resolve relative credential paths against the project root."""
        path = Path(value)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return str(path.resolve())

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def uploads_dir(self) -> Path:
        directory = PROJECT_ROOT / "uploads"
        directory.mkdir(parents=True, exist_ok=True)
        return directory


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
