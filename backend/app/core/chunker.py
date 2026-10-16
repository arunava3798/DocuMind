"""Split documents into overlapping chunks for embedding and retrieval."""
from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from ..config import get_settings


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split documents into overlapping chunks while preserving metadata."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_documents(documents)
