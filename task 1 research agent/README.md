# Personalized AI Research Agent

This is a secure Streamlit demo for the assessment task: **Build Personalized AI Agents**.

It implements a research agent that takes a topic, searches uploaded/local documents with RAG, can optionally search the web, summarizes the answer, and cites sources.

## What It Shows

- **System prompt:** See `prompts/system_prompt.txt` and the sidebar expander in the app.
- **Memory:** Conversation history is stored in the Streamlit session and shown in the Memory panel.
- **RAG:** Documents are chunked, embedded, and retrieved from ChromaDB.
- **Tool calling:** The LLM can call `retrieve_documents` and, when enabled, `web_search`.
- **Guardrails:** If sources do not answer the question, the prompt requires: `I don't know based on the available sources.`

## Tech Stack

- Python
- LangChain
- OpenAI or Gemini API
- ChromaDB
- Streamlit

## Setup

Use Python 3.10 or newer. On this Windows machine, Python 3.13 is available through `py -3.13`.

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Add either `OPENAI_API_KEY` or `GOOGLE_API_KEY` to `.env`.

Run:

```bash
streamlit run app.py
```

## Using the App

1. Choose OpenAI or Gemini in the sidebar.
2. Add an API key in `.env` or paste it into the password field.
3. Upload PDF, DOCX, TXT, or MD files if you want custom research material.
4. Click **Build / Refresh RAG Index**.
5. Ask a research question.
6. Review the answer, source citations, memory, and tool calls.

## Secure Google Drive Upload Checklist

Upload these files/folders:

- `app.py`
- `src/`
- `prompts/`
- `knowledge_base/`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `README.md`
- `SECURITY.md`

Do **not** upload:

- `.env`
- `.streamlit/secrets.toml`
- `data/uploads/`
- `chroma_db/`
- any private documents, keys, or generated logs

The included `.gitignore` is configured to exclude these sensitive/generated paths.
