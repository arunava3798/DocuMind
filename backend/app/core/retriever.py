"""Retrieval orchestration: dense + sparse hybrid search, RRF fusion, multi-query, re-ranking."""
from __future__ import annotations

from langchain_core.documents import Document
from sqlalchemy import text

from ..config import get_settings
from ..db.database import init_engine
from ..observability import metrics
from . import query_rewrite, reranker, vectorstore

# Sparse retrieval via Postgres full-text search over pgvector's chunk text column.
_SPARSE_SQL = text(
    """
    SELECT e.document AS document, e.cmetadata AS cmetadata
    FROM langchain_pg_embedding e
    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
    WHERE c.name = :collection
      AND to_tsvector('english', e.document) @@ websearch_to_tsquery('english', :q)
    ORDER BY ts_rank(
        to_tsvector('english', e.document),
        websearch_to_tsquery('english', :q)
    ) DESC
    LIMIT :limit
    """
)


def dense_retrieve(query: str, k: int) -> list[Document]:
    try:
        return vectorstore.similarity_search(query, k=k)
    except Exception:
        return []


def sparse_retrieve(query: str, k: int) -> list[Document]:
    settings = get_settings()
    try:
        engine = init_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                _SPARSE_SQL,
                {"collection": settings.pg_collection_name, "q": query, "limit": k},
            ).fetchall()
    except Exception:
        return []
    return [Document(page_content=row.document, metadata=row.cmetadata or {}) for row in rows]


def reciprocal_rank_fusion(result_lists: list[list[Document]], k: int = 60) -> list[Document]:
    """Fuse multiple ranked lists into one using Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    docs_by_key: dict[str, Document] = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            key = doc.metadata.get("chunk_id") or doc.page_content
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            docs_by_key[key] = doc
    ranked_keys = sorted(scores, key=scores.get, reverse=True)
    return [docs_by_key[key] for key in ranked_keys]


def retrieve(question: str) -> list[Document]:
    """Full retrieval pipeline: multi-query -> hybrid/dense -> RRF -> optional re-rank."""
    with metrics.timed("retrieval_ms"):
        settings = get_settings()

        queries = (
            query_rewrite.generate_subqueries(question, settings.num_queries)
            if settings.multi_query_enabled
            else [question]
        )

        result_lists: list[list[Document]] = []
        for query in queries:
            result_lists.append(dense_retrieve(query, settings.retrieval_candidates))
            if settings.retrieval_mode == "hybrid":
                result_lists.append(sparse_retrieve(query, settings.retrieval_candidates))

        fused = reciprocal_rank_fusion(result_lists)
        candidates = fused[: settings.retrieval_candidates]

        if settings.rerank_enabled and candidates:
            return reranker.rerank(question, candidates, settings.top_k)
        return candidates[: settings.top_k]
