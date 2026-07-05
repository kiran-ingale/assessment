# AI Document Automation

Production-ready FastAPI service that accepts PDF uploads, extracts text, analyzes documents with OpenAI, logs results to Google Sheets, and emails a structured summary.

## Features

- PDF upload endpoint with validation and size limits
- Text extraction using `pdfplumber` with `PyPDF2` fallback
- OpenAI-powered structured analysis:
  - Summary (150–250 words)
  - Key points
  - Action items
  - Deadlines
  - Important entities (names, organizations, dates)
- Google Sheets logging via `gspread`
- HTML email delivery via SMTP
- Structured JSON API responses
- Logging, type hints, docstrings, and modular services

## Project Structure

```
ai-document-automation/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── postman_collection.json
├── services/
│   ├── pdf_service.py
│   ├── ai_service.py
│   ├── sheets_service.py
│   └── email_service.py
├── utils/
│   ├── config.py
│   ├── exceptions.py
│   ├── helpers.py
│   ├── logger.py
│   └── models.py
├── credentials/
│   └── README.md
└── uploads/
```

## Security Before Uploading to Google Drive

This project handles sensitive credentials and document content. 

### Safe to upload

- All source code (`.py` files)
- `requirements.txt`
- `.env.example` (template only — no real keys)
- `README.md`
- `postman_collection.json`
- `.gitignore`
- `credentials/README.md`
- Empty placeholder files (`.gitkeep`)



## Prerequisites

- Python 3.12+
- OpenAI API key
- Google Cloud service account with Sheets + Drive API access
- A Google Sheet shared with the service account email
- SMTP credentials (Gmail App Password recommended)

## Installation

### 1. Clone or download the project

```bash
cd ai-document-automation
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
copy .env.example .env
```

On macOS/Linux:

```bash
cp .env.example .env
```

Edit `.env` and set your real values locally. **Keep this file private.**

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
GOOGLE_SHEET_NAME=Document Automation Log
GOOGLE_SERVICE_ACCOUNT_JSON=credentials/service-account.json
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SENDER_EMAIL=your-email@gmail.com
RECEIVER_EMAIL=recipient@example.com
MAX_UPLOAD_SIZE_MB=10
```

## External Service Setup

### OpenAI

1. Sign in at [https://platform.openai.com/](https://platform.openai.com/).
2. Create an API key under **API keys**.
3. Add the key to `.env` as `OPENAI_API_KEY`.
4. Optionally change `OPENAI_MODEL` (default: `gpt-4o-mini`).

### Google Sheets

1. Open [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable:
   - Google Sheets API
   - Google Drive API
3. Create a **Service Account** and download the JSON key.
4. Save the key as `credentials/service-account.json` (this path is gitignored).
5. Create a Google Sheet (e.g. `Document Automation Log`).
6. Share the sheet with the service account email (`client_email` in the JSON file) as **Editor**.
7. Set `GOOGLE_SHEET_NAME` in `.env` to the exact sheet title.

The first API call will auto-create these column headers:

| Timestamp | Filename | Summary | Key Points | Action Items | Deadlines | Entities |

### Gmail / SMTP

For Gmail:

1. Enable 2-Step Verification on your Google account.
2. Generate an **App Password** at [https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
3. Use these settings:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SENDER_EMAIL=your-email@gmail.com
RECEIVER_EMAIL=recipient@example.com
```

Other SMTP providers (Outlook, SendGrid, etc.) work by updating `SMTP_HOST`, `SMTP_PORT`, and credentials accordingly.

## Running the Server

From the project root:

```bash
uvicorn app:app --reload
```

- API: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Service info |
| GET | `/health` | Health and configuration status |
| POST | `/upload` | Upload and analyze a PDF |

### Upload Request

- **Content-Type:** `multipart/form-data`
- **Field:** `file` (PDF only)

### Example curl Command

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/document.pdf"
```

**Windows PowerShell:**

```powershell
curl.exe -X POST "http://127.0.0.1:8000/upload" `
  -H "accept: application/json" `
  -F "file=@C:\path\to\document.pdf"
```

### Example Success Response

```json
{
  "success": true,
  "filename": "document.pdf",
  "summary": "This document outlines...",
  "key_points": [
    "First key point",
    "Second key point"
  ],
  "action_items": [
    "Review contract terms by Friday",
    "Schedule follow-up meeting"
  ],
  "deadlines": [
    "March 15, 2026"
  ],
  "important_entities": [
    "Acme Corp",
    "John Smith",
    "March 15, 2026"
  ],
  "sheet_updated": true,
  "email_sent": true
}
```

### Example Error Response

```json
{
  "success": false,
  "error": "Unable to extract text from PDF. The document may be scanned, image-only, or empty.",
  "details": {
    "filename": "scan.pdf",
    "hint": "Use OCR preprocessing for scanned documents before upload."
  }
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Successful analysis |
| 400 | Invalid or non-PDF upload |
| 413 | File exceeds size limit |
| 422 | PDF contains no extractable text |
| 500 | Missing configuration or unexpected server error |
| 502 | OpenAI, Google Sheets, or email integration failure |

Note: If Google Sheets or email fails after a successful AI analysis, the API still returns `200` with `sheet_updated: false` or `email_sent: false` so you retain the analysis payload.

## Postman Collection

Import `postman_collection.json` into Postman:

1. Open Postman → **Import**
2. Select `postman_collection.json`
3. Set the `base_url` variable (default: `http://127.0.0.1:8000`)
4. Use **Upload PDF** and attach a local PDF file

## Error Handling

The application handles:

- Invalid or empty PDF uploads
- Scanned/image-only PDFs with no extractable text
- OpenAI API failures and malformed JSON responses
- Missing or invalid Google credentials
- Google Sheet access errors
- SMTP authentication and delivery failures
- Missing environment variables at startup

## Logging

Structured logs are written to stdout:

```
2026-07-04 20:30:15 | INFO     | services.pdf_service | Extracted 4521 characters from report.pdf
```

## Development Notes

- Uploaded PDFs are stored in `uploads/` with a UUID prefix (also gitignored).
- LLM responses use OpenAI JSON mode for reliable parsing.
- Long documents are truncated to 120,000 characters before LLM analysis.
- Modular services can be tested independently.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Application is not configured` | Copy `.env.example` to `.env` and fill all values |
| `Google service account credentials file was not found` | Place JSON at path in `GOOGLE_SERVICE_ACCOUNT_JSON` |
| `Configured Google Sheet was not found` | Verify sheet name and share with service account email |
| Gmail SMTP authentication failed | Use an App Password, not your regular Gmail password |
| Empty PDF text | Document is likely scanned; run OCR before upload |
| OpenAI errors | Check API key, billing, and model availability |

## License

MIT — use freely for learning, assessment, and production deployments with proper secret management.
