"""Cross-encoder re-ranking to improve precision of the retrieved candidates."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.documents import Document

from ..config import get_settings


@lru_cache
def get_reranker():
    """Lazily load the cross-encoder model (downloads once, then cached)."""
    from sentence_transformers import CrossEncoder

    return CrossEncoder(get_settings().rerank_model)


def rerank(query: str, docs: list[Document], top_k: int) -> list[Document]:
    """Re-score (query, chunk) pairs with the cross-encoder and keep the best top_k."""
    if not docs:
        return []
    model = get_reranker()
    scores = model.predict([(query, doc.page_content) for doc in docs])
    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
    return [doc for doc, _ in ranked[:top_k]]
