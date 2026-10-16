"""Load and extract plain text from PDF, TXT, and DOCX files."""
from __future__ import annotations

import os
from typing import Iterable

from langchain_community.document_loaders import (
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def _loader_for(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return PyPDFLoader(path)
    if ext == ".docx":
        return Docx2txtLoader(path)
    if ext == ".txt":
        return TextLoader(path, encoding="utf-8")
    raise ValueError(f"Unsupported file type: {ext}")


def load_file(path: str) -> list[Document]:
    """Load a single file into a list of LangChain Documents."""
    docs = _loader_for(path).load()
    filename = os.path.basename(path)
    for doc in docs:
        doc.metadata["source"] = filename
    return docs


def load_paths(paths: Iterable[str]) -> list[Document]:
    """Load several files given their paths."""
    documents: list[Document] = []
    for path in paths:
        documents.extend(load_file(path))
    return documents
