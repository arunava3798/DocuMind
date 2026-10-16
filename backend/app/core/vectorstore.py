"""Postgres + pgvector vector store (Phase 2). Document metadata lives in the `documents` table."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.documents import Document
from langchain_postgres import PGVector

from ..config import get_settings
from ..db.database import normalize_db_url
from .embeddings import get_embeddings


@lru_cache
def get_vectorstore() -> PGVector:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env.")
    return PGVector(
        embeddings=get_embeddings(),
        collection_name=settings.pg_collection_name,
        connection=normalize_db_url(settings.database_url),
        use_jsonb=True,
    )


def add_documents(chunks: list[Document], ids: list[str]) -> None:
    """Add chunks (with explicit ids so they can be deleted later) to pgvector."""
    get_vectorstore().add_documents(chunks, ids=ids)


def similarity_search(query: str, k: int) -> list[Document]:
    return get_vectorstore().similarity_search(query, k=k)


def delete_ids(ids: list[str]) -> None:
    """Remove specific chunk vectors by their ids."""
    if ids:
        get_vectorstore().delete(ids=ids)

