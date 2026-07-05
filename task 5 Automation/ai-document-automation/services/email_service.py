"""Email delivery service using SMTP."""

from __future__ import annotations

import smtplib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from utils.config import Settings
from utils.exceptions import EmailServiceError
from utils.logger import get_logger
from utils.models import DocumentAnalysis

logger = get_logger(__name__)


class EmailService:
    """Send professional HTML summary emails via SMTP."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_summary_email(self, filename: str, analysis: DocumentAnalysis) -> None:
        """
        Send analysis summary to the configured receiver address.

        Raises:
            EmailServiceError: If SMTP delivery fails.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        subject = f"Document Analysis Summary: {filename}"
        html_body = self._build_html_email(filename, analysis, timestamp)
        text_body = self._build_text_email(filename, analysis, timestamp)

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.settings.sender_email
        message["To"] = self.settings.receiver_email
        message.attach(MIMEText(text_body, "plain", "utf-8"))
        message.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.settings.smtp_user, self.settings.smtp_password)
                server.sendmail(
                    self.settings.sender_email,
                    [self.settings.receiver_email],
                    message.as_string(),
                )
            logger.info("Summary email sent for %s to %s", filename, self.settings.receiver_email)
        except Exception as exc:
            logger.exception("Failed to send summary email for %s", filename)
            raise EmailServiceError(
                "Failed to send summary email.",
                details={"reason": str(exc)},
            ) from exc

    def _build_html_email(
        self,
        filename: str,
        analysis: DocumentAnalysis,
        timestamp: str,
    ) -> str:
        """Build a professional HTML email body."""
        key_points_html = self._render_list(analysis.key_points)
        action_items_html = self._render_list(analysis.action_items)
        deadlines_html = self._render_list(analysis.deadlines) or "<p><em>No deadlines mentioned.</em></p>"
        entities_html = self._render_list(analysis.important_entities) or "<p><em>No notable entities found.</em></p>"

        return f"""\
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Document Analysis Summary</title>
  </head>
  <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.5;">
    <div style="max-width: 720px; margin: 0 auto; padding: 24px;">
      <h2 style="color: #1f2937;">Document Analysis Summary</h2>
      <p><strong>Document:</strong> {escape(filename)}</p>
      <p><strong>Generated:</strong> {escape(timestamp)}</p>

      <h3 style="color: #374151;">Summary</h3>
      <p>{escape(analysis.summary)}</p>

      <h3 style="color: #374151;">Key Points</h3>
      {key_points_html}

      <h3 style="color: #374151;">Action Items</h3>
      {action_items_html}

      <h3 style="color: #374151;">Deadlines</h3>
      {deadlines_html}

      <h3 style="color: #374151;">Important Entities</h3>
      {entities_html}

      <hr style="margin-top: 32px; border: none; border-top: 1px solid #e5e7eb;">
      <p style="font-size: 12px; color: #6b7280;">
        This message was generated automatically by the AI Document Automation service.
      </p>
    </div>
  </body>
</html>
"""

    def _build_text_email(
        self,
        filename: str,
        analysis: DocumentAnalysis,
        timestamp: str,
    ) -> str:
        """Build a plain-text fallback email body."""
        sections = [
            "Document Analysis Summary",
            f"Document: {filename}",
            f"Generated: {timestamp}",
            "",
            "Summary",
            analysis.summary,
            "",
            "Key Points",
            self._render_text_list(analysis.key_points),
            "",
            "Action Items",
            self._render_text_list(analysis.action_items),
            "",
            "Deadlines",
            self._render_text_list(analysis.deadlines) or "No deadlines mentioned.",
            "",
            "Important Entities",
            self._render_text_list(analysis.important_entities) or "No notable entities found.",
        ]
        return "\n".join(sections)

    @staticmethod
    def _render_list(items: list[str]) -> str:
        if not items:
            return "<p><em>None found.</em></p>"
        list_items = "".join(f"<li>{escape(item)}</li>" for item in items)
        return f"<ul>{list_items}</ul>"

    @staticmethod
    def _render_text_list(items: list[str]) -> str:
        if not items:
            return "- None found."
        return "\n".join(f"- {item}" for item in items)
