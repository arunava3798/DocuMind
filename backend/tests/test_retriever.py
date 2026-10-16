"""Unit tests for Reciprocal Rank Fusion (pure function, offline)."""
from langchain_core.documents import Document

from app.core.retriever import reciprocal_rank_fusion


def _doc(chunk_id: str) -> Document:
    return Document(page_content=f"content {chunk_id}", metadata={"chunk_id": chunk_id})


def test_rrf_rewards_agreement_across_lists():
    # "b" appears high in both lists -> should rank first after fusion.
    dense = [_doc("a"), _doc("b"), _doc("c")]
    sparse = [_doc("b"), _doc("d"), _doc("a")]

    fused = reciprocal_rank_fusion([dense, sparse])
    order = [d.metadata["chunk_id"] for d in fused]

    assert order[0] == "b"
    assert set(order) == {"a", "b", "c", "d"}


def test_rrf_handles_empty_lists():
    assert reciprocal_rank_fusion([[], []]) == []
