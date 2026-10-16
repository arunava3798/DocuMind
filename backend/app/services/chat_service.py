"""Chat service: history-aware retrieval and grounded answer generation with sources."""
from __future__ import annotations

from langchain_core.documents import Document

from ..core import query_rewrite, retriever
from ..core.llm import generate

PROMPT_TEMPLATE = (
    "You are a helpful assistant that answers questions using ONLY the provided "
    "context. If the answer is not in the context, say you don't know. "
    "Be concise and cite facts from the context.\n\n"
    "{history}"
    "Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
)


def _format_context(docs: list[Document]) -> str:
    blocks = []
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        blocks.append(f"[{i}] (source: {source})\n{doc.page_content}")
    return "\n\n".join(blocks)


def _format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    return f"Conversation so far:\n{lines}\n\n"


def answer_question(
    question: str, history: list[dict] | None = None, k: int | None = None
) -> tuple[str, list[dict]]:
    """Return a grounded answer and its source chunks, using conversation history."""
    history = history or []
    standalone = query_rewrite.condense_question(question, history)
    docs = retriever.retrieve(standalone)
    prompt = PROMPT_TEMPLATE.format(
        history=_format_history(history),
        context=_format_context(docs),
        question=question,
    )
    answer = generate(prompt)
    sources = [
        {"source": doc.metadata.get("source", "unknown"), "content": doc.page_content[:500]}
        for doc in docs
    ]
    return answer, sources
