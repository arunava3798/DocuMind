"""LLM-assisted query transformation: condense follow-ups and generate multi-query variants."""
from __future__ import annotations

from .llm import generate

_CONDENSE_PROMPT = (
    "Given the conversation history and a follow-up question, rewrite the follow-up "
    "as a standalone question that can be understood without the history. "
    "Return only the rewritten question.\n\n"
    "Conversation:\n{history}\n\nFollow-up: {question}\n\nStandalone question:"
)

_MULTIQUERY_PROMPT = (
    "Generate {n} alternative search queries for the question below, using different "
    "wording and synonyms. One query per line, no numbering or bullets.\n\n"
    "Question: {question}"
)


def condense_question(question: str, history: list[dict]) -> str:
    """Rewrite a follow-up into a standalone question using the conversation history."""
    if not history:
        return question
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    prompt = _CONDENSE_PROMPT.format(history=history_text, question=question)
    try:
        rewritten = generate(prompt).strip()
        return rewritten or question
    except Exception:
        return question


def generate_subqueries(question: str, num_queries: int) -> list[str]:
    """Return the original question plus (num_queries - 1) LLM-generated variants."""
    if num_queries <= 1:
        return [question]
    prompt = _MULTIQUERY_PROMPT.format(n=num_queries - 1, question=question)
    try:
        text = generate(prompt)
        variants = [line.strip("-•* ").strip() for line in text.splitlines() if line.strip()]
    except Exception:
        variants = []
    return [question] + variants[: num_queries - 1]
