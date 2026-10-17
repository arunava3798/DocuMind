"""Chat service: history-aware retrieval and grounded answer generation with sources."""
from __future__ import annotations

from langchain_core.documents import Document

from ..core import query_rewrite, retriever
from ..core.llm import generate

PROMPT_TEMPLATE = (
    "You are a helpful, friendly assistant. Answer the user's question directly and "
    "conversationally.\n"
    "The reference material below is drawn from the user's uploaded documents.\n"
    "Guidelines:\n"
    "- If the reference material answers the question, use it and answer naturally.\n"
    "- If it does not answer the question (or is empty or unrelated), answer from your "
    "own general knowledge and begin your reply with exactly: "
    "\"This isn't in your documents, but \".\n"
    "- Do not mention the words 'context' or 'reference material', and do not add "
    "bracketed citation markers like [1].\n\n"
    "{history}"
    "Reference material:\n{context}\n\nQuestion: {question}\n\nAnswer:"
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
