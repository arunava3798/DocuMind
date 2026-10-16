"""Unit tests for document chunking (offline, no network/DB)."""
from langchain_core.documents import Document

from app.core.chunker import chunk_documents


def test_chunking_splits_long_text_and_preserves_metadata():
    text = " ".join(f"This is sentence number {i} with some filler words." for i in range(400))
    docs = [Document(page_content=text, metadata={"source": "doc.txt"})]

    chunks = chunk_documents(docs)

    assert len(chunks) > 1
    assert all(chunk.metadata["source"] == "doc.txt" for chunk in chunks)
    assert all(chunk.page_content for chunk in chunks)


def test_chunking_short_text_single_chunk():
    docs = [Document(page_content="short text", metadata={"source": "s.txt"})]
    chunks = chunk_documents(docs)
    assert len(chunks) == 1
    assert chunks[0].page_content == "short text"
