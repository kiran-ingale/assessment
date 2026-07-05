"""Google Sheets integration service."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials

from utils.config import Settings
from utils.exceptions import ConfigurationError, SheetsServiceError
from utils.helpers import join_list_for_sheet
from utils.logger import get_logger
from utils.models import DocumentAnalysis

logger = get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

HEADERS = [
    "Timestamp",
    "Filename",
    "Summary",
    "Key Points",
    "Action Items",
    "Deadlines",
    "Entities",
]


class SheetsService:
    """Append document analysis rows to a Google Sheet."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: gspread.Client | None = None

    def append_analysis(self, filename: str, analysis: DocumentAnalysis) -> None:
        """
        Append one analysis row to the configured Google Sheet.

        Raises:
            SheetsServiceError: If Google Sheets update fails.
            ConfigurationError: If credentials are missing or invalid.
        """
        try:
            worksheet = self._get_worksheet()
            self._ensure_headers(worksheet)

            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            row = [
                timestamp,
                filename,
                analysis.summary,
                join_list_for_sheet(analysis.key_points),
                join_list_for_sheet(analysis.action_items),
                join_list_for_sheet(analysis.deadlines),
                join_list_for_sheet(analysis.important_entities),
            ]
            worksheet.append_row(row, value_input_option="USER_ENTERED")
            logger.info("Appended analysis for %s to Google Sheet.", filename)
        except (ConfigurationError, SheetsServiceError):
            raise
        except Exception as exc:
            logger.exception("Google Sheets update failed for %s", filename)
            raise SheetsServiceError(
                "Failed to update Google Sheet.",
                details={"reason": str(exc)},
            ) from exc

    def _get_client(self) -> gspread.Client:
        """Create or return cached gspread client."""
        if self._client is not None:
            return self._client

        credentials_path = Path(self.settings.google_service_account_json)
        if not credentials_path.exists():
            raise ConfigurationError(
                "Google service account credentials file was not found.",
                details={"expected_path": str(credentials_path)},
            )

        try:
            credentials = Credentials.from_service_account_file(
                str(credentials_path),
                scopes=SCOPES,
            )
            self._client = gspread.authorize(credentials)
            return self._client
        except Exception as exc:
            logger.exception("Failed to initialize Google Sheets client.")
            raise ConfigurationError(
                "Invalid Google service account credentials.",
                details={"reason": str(exc)},
            ) from exc

    def _get_worksheet(self) -> gspread.Worksheet:
        """Open the configured spreadsheet and return the first worksheet."""
        try:
            client = self._get_client()
            spreadsheet = client.open(self.settings.google_sheet_name)
            return spreadsheet.sheet1
        except gspread.SpreadsheetNotFound as exc:
            raise SheetsServiceError(
                "Configured Google Sheet was not found.",
                details={
                    "sheet_name": self.settings.google_sheet_name,
                    "hint": "Ensure the sheet exists and is shared with the service account email.",
                },
            ) from exc
        except Exception as exc:
            logger.exception("Unable to open Google Sheet.")
            raise SheetsServiceError(
                "Unable to access Google Sheet.",
                details={"reason": str(exc)},
            ) from exc

    @staticmethod
    def _ensure_headers(worksheet: gspread.Worksheet) -> None:
        """Write header row when the sheet is empty."""
        existing = worksheet.get_all_values()
        if not existing:
            worksheet.append_row(HEADERS, value_input_option="USER_ENTERED")
