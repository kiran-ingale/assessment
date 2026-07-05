from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, Tuple

from langchain_chroma import Chroma
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def build_embeddings(provider: str, api_key: str, model_name: str):
    provider = provider.lower()
    if provider == "openai":
        return OpenAIEmbeddings(model=model_name, api_key=api_key)
    if provider == "gemini":
        return GoogleGenerativeAIEmbeddings(model=model_name, google_api_key=api_key)
    raise ValueError(f"Unsupported provider: {provider}")


def supported_files(paths: Iterable[Path]) -> list:
    return [path for path in paths if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS]


def load_document(path: Path) -> list:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix == ".docx":
        loader = Docx2txtLoader(str(path))
    elif suffix in {".txt", ".md"}:
        loader = TextLoader(str(path), encoding="utf-8")
    else:
        raise ValueError(f"Unsupported document type: {path.suffix}")

    docs = loader.load()
    for doc in docs:
        doc.metadata["source"] = path.name
    return docs


def load_documents(paths: Iterable[Path]) -> list:
    documents = []
    for path in supported_files(paths):
        documents.extend(load_document(path))
    return documents


def split_documents(documents: list) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=140,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks, start=1):
        chunk.metadata["chunk_id"] = index
    return chunks


def rebuild_vector_store(
    *,
    document_paths: Iterable[Path],
    persist_dir: Path,
    collection_name: str,
    embeddings,
) -> Tuple[Chroma, int]:
    documents = load_documents(document_paths)
    chunks = split_documents(documents)

    if persist_dir.exists():
        shutil.rmtree(persist_dir)
    persist_dir.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=collection_name,
        persist_directory=str(persist_dir),
    )
    return vector_store, len(chunks)


def load_vector_store(*, persist_dir: Path, collection_name: str, embeddings) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        persist_directory=str(persist_dir),
        embedding_function=embeddings,
    )


def make_retriever(vector_store: Chroma, k: int = 5) -> VectorStoreRetriever:
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})
