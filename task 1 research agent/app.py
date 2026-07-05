from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage

from src.agent import build_agent_executor, load_system_prompt, run_research, summarize_tool_calls
from src.rag import build_embeddings, load_vector_store, make_retriever, rebuild_vector_store
from src.security import mask_secret, sanitize_filename


BASE_DIR = Path(__file__).parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge_base"
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
DEFAULT_CHROMA_DIR = BASE_DIR / os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
COLLECTION_NAME = "personalized_research_agent"


def init_state() -> None:
    st.session_state.setdefault("chat_history", [])
    st.session_state.setdefault("indexed_chunks", 0)
    st.session_state.setdefault("last_tool_calls", [])


def css() -> None:
    st.markdown(
        """
        <style>
        .main .block-container { max-width: 1120px; padding-top: 1.2rem; }
        [data-testid="stSidebar"] { min-width: 330px; }
        .small-muted { color: #667085; font-size: 0.9rem; }
        .status-ok { color: #067647; font-weight: 600; }
        .status-warn { color: #B42318; font-weight: 600; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def collect_document_paths() -> List[Path]:
    paths = []
    if KNOWLEDGE_DIR.exists():
        paths.extend(KNOWLEDGE_DIR.glob("*"))
    if UPLOAD_DIR.exists():
        paths.extend(UPLOAD_DIR.glob("*"))
    return paths


def save_uploads(uploaded_files) -> List[Path]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    for uploaded_file in uploaded_files:
        safe_name = sanitize_filename(uploaded_file.name)
        target = UPLOAD_DIR / safe_name
        target.write_bytes(uploaded_file.getbuffer())
        saved.append(target)
    return saved


def provider_defaults(provider: str) -> Tuple[str, str, Optional[str]]:
    if provider == "OpenAI":
        return (
            os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            os.getenv("OPENAI_API_KEY"),
        )
    return (
        os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004"),
        os.getenv("GOOGLE_API_KEY"),
    )


def render_memory(history: List[BaseMessage]) -> None:
    if not history:
        st.info("No conversation memory yet. Ask a research question to start a session.")
        return
    for message in history[-8:]:
        role = "user" if message.type == "human" else "assistant"
        with st.chat_message(role):
            st.markdown(message.content)


def main() -> None:
    load_dotenv()
    st.set_page_config(page_title="Personalized AI Research Agent", layout="wide")
    init_state()
    css()

    system_prompt = load_system_prompt(BASE_DIR / "prompts" / "system_prompt.txt")

    st.title("Personalized AI Research Agent")
    st.caption("Document RAG + optional web search + session memory + strict citations.")

    with st.sidebar:
        st.header("Configuration")
        provider = st.selectbox("Model provider", ["OpenAI", "Gemini"], index=0)
        default_model, default_embedding, env_key = provider_defaults(provider)
        provider_key = "openai" if provider == "OpenAI" else "gemini"

        api_key = st.text_input(
            "API key",
            value="",
            type="password",
            help="Kept only in this Streamlit session unless you put it in a local .env file.",
            placeholder=f"Using env: {mask_secret(env_key)}",
        ) or env_key

        model_name = st.text_input("Chat model", value=default_model)
        embedding_model = st.text_input("Embedding model", value=default_embedding)
        allow_web_search = st.toggle(
            "Allow web search tool",
            value=os.getenv("ALLOW_WEB_SEARCH", "false").lower() == "true",
        )

        st.divider()
        st.subheader("Knowledge Base")
        uploaded_files = st.file_uploader(
            "Upload PDF, DOCX, TXT, or MD files",
            type=["pdf", "docx", "txt", "md"],
            accept_multiple_files=True,
        )
        if uploaded_files:
            saved = save_uploads(uploaded_files)
            st.success(f"Saved {len(saved)} file(s) locally for indexing.")

        if st.button("Build / Refresh RAG Index", type="primary", use_container_width=True):
            if not api_key:
                st.error("Add an API key first. The key is required to create embeddings.")
            else:
                try:
                    embeddings = build_embeddings(provider_key, api_key, embedding_model)
                    vector_store, chunk_count = rebuild_vector_store(
                        document_paths=collect_document_paths(),
                        persist_dir=DEFAULT_CHROMA_DIR,
                        collection_name=COLLECTION_NAME,
                        embeddings=embeddings,
                    )
                    st.session_state.indexed_chunks = chunk_count
                    st.success(f"Indexed {chunk_count} chunks in ChromaDB.")
                except Exception as exc:
                    st.error(f"Indexing failed: {exc}")

        st.markdown(f"Indexed chunks: **{st.session_state.indexed_chunks}**")

        with st.expander("System prompt", expanded=False):
            st.code(system_prompt, language="text")

        with st.expander("Security checklist", expanded=False):
            st.markdown(
                """
                - Keep real keys in `.env` or the password field.
                - Do not upload `.env`, `.streamlit/secrets.toml`, `data/uploads/`, or `chroma_db/`.
                - The included `.gitignore` excludes generated data and secrets.
                """
            )

    left, right = st.columns([0.62, 0.38], gap="large")

    with left:
        st.subheader("Research")
        topic = st.text_area(
            "Topic or question",
            placeholder="Example: Explain how this project demonstrates system prompt, memory, RAG, tool calling, and guardrails.",
            height=120,
        )
        run_button = st.button("Run Research Agent", type="primary", disabled=not topic.strip())

        if run_button:
            if not api_key:
                st.error("Add an API key in the sidebar or local .env file.")
            else:
                try:
                    embeddings = build_embeddings(provider_key, api_key, embedding_model)
                    if not DEFAULT_CHROMA_DIR.exists():
                        with st.spinner("Building the first RAG index from sample/local documents..."):
                            _, chunk_count = rebuild_vector_store(
                                document_paths=collect_document_paths(),
                                persist_dir=DEFAULT_CHROMA_DIR,
                                collection_name=COLLECTION_NAME,
                                embeddings=embeddings,
                            )
                            st.session_state.indexed_chunks = chunk_count

                    vector_store = load_vector_store(
                        persist_dir=DEFAULT_CHROMA_DIR,
                        collection_name=COLLECTION_NAME,
                        embeddings=embeddings,
                    )
                    retriever = make_retriever(vector_store)
                    executor = build_agent_executor(
                        provider=provider_key,
                        api_key=api_key,
                        model_name=model_name,
                        retriever=retriever,
                        allow_web_search=allow_web_search,
                        system_prompt=system_prompt,
                    )

                    with st.spinner("Researching with tools and checking sources..."):
                        result = run_research(
                            executor=executor,
                            topic=topic,
                            chat_history=st.session_state.chat_history,
                        )
                    st.session_state.last_tool_calls = summarize_tool_calls(result)
                    st.markdown(result["output"])
                except Exception as exc:
                    st.error(f"Research failed: {exc}")

    with right:
        st.subheader("Memory")
        render_memory(st.session_state.chat_history)

        st.subheader("Tool Calls")
        if st.session_state.last_tool_calls:
            for call in st.session_state.last_tool_calls:
                st.code(call, language="text")
        else:
            st.info("Tool calls will appear after a research run.")


if __name__ == "__main__":
    main()
