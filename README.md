# GenAI Client Intelligence

A small Streamlit prototype that extracts text from uploaded conversation PDFs and produces a coaching dashboard. The app uses Mistral or Groq (llama) LLMs when API keys are configured in `.env`; otherwise it falls back to a built-in heuristic analyzer so the UI still renders offline.

## Features

- Upload PDF conversations and extract text via `pypdf`.
- Heuristic analysis fallback when no API keys are present.
- Calls Mistral (`MISTRAL_API_KEY`, `MISTRAL_MODEL`) or Groq (`GROQ_API_KEY`, `GROQ_MODEL`) based on selection and `.env`.
- Dashboard with nutrition, sleep, water, exercise, stress, risk flags, and recommendations.

## Setup

1. Create a Python 3.10+ virtual environment (Windows example):

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Add your API keys to a `.env` file in the project root. Example `.env`:

```
MISTRAL_API_KEY="your_mistral_key_here"
GROQ_API_KEY="your_groq_key_here"
LLM_PROVIDER=mistral
MISTRAL_MODEL=mistral-small-latest
GROQ_MODEL=llama-3.1-8b-instant
```

Note: `.env` is ignored by the repository's `.gitignore` by default. Do NOT commit secrets.

## Run

```powershell
py -3 -m streamlit run app.py
```

Open the app at `http://localhost:8501`.

## Files of interest

- `app.py` — Streamlit application and analysis logic
- `.env` — API keys and default provider/model (not committed)
- `.gitignore` — ignores `.env` and common artifacts

## Troubleshooting

- If the app shows the heuristic result despite keys being present, confirm keys are available to the Python process (`os.getenv`) and that the configured provider matches the model selection in the sidebar.
- If you need to stop tracking a previously committed `.env`, run:

```bash
git rm --cached .env
git commit -m "Stop tracking .env"
```

## License

Private prototype — adapt as needed.# GenAI Client Intelligence

Lightweight Streamlit prototype that analyzes uploaded conversation PDFs and produces a coaching dashboard. Uses Mistral or Groq (llama) LLMs when API keys are configured, otherwise falls back to a local heuristic analyzer.

## Requirements
- Python 3.11+ (project originally tested with Python 3.13 on Windows)
- pip

Install runtime dependencies:

```bash
py -3 -m pip install --upgrade pip
py -3 -m pip install streamlit requests python-dotenv pypdf pandas
```

## Environment
Create a `.env` file in the project root with the following variables (do NOT commit this file):

```
MISTRAL_API_KEY="your_mistral_key"
GROQ_API_KEY="your_groq_key"
LLM_PROVIDER=mistral
MISTRAL_MODEL=mistral-small-latest
GROQ_MODEL=llama-3.1-8b-instant
```

.gitignore in this repo already excludes `.env` so secrets won't be committed.

If no API keys are present the app automatically uses a built-in `heuristic_analysis()` fallback so the dashboard still renders.

## Run

Start the Streamlit app:

```bash
py -3 -m streamlit run app.py
```

Open http://localhost:8501 in your browser. Use the sidebar to upload a PDF and select one of: `heuristic`, `mistral-small-latest`, or `llama-3.1-8b-instant`.

## Notes
- Uploaded PDFs are saved to the `uploads/` folder.
- To stop tracking an already-committed `.env` file:

```bash
git rm --cached .env
git commit -m "Stop tracking .env"
```

Want me to also create a `requirements.txt` and add a short developer checklist? Reply and I'll add them.
