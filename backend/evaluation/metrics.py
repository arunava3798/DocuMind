"""RAGAS-style RAG metrics computed with our own LLM + embeddings (no heavy deps).

- context_recall / context_precision: deterministic, keyword-grounded (no LLM calls).
- faithfulness: LLM-as-judge (is the answer supported by the retrieved context?).
- answer_relevancy: embedding similarity between the question and the answer.
- answer_correctness: embedding similarity between the answer and a reference answer.
"""
from __future__ import annotations

import re

import numpy as np

from app.core.embeddings import get_embeddings
from app.core.llm import generate

_FAITHFULNESS_PROMPT = (
    "You are grading whether an ANSWER is fully supported by the given CONTEXT. "
    "Reply with a single number between 0 and 1 (1 = every claim is supported by the "
    "context, 0 = not supported at all). Reply with the number only.\n\n"
    "CONTEXT:\n{context}\n\nANSWER:\n{answer}\n\nScore:"
)


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a), np.asarray(b)
    return float(va @ vb / ((np.linalg.norm(va) * np.linalg.norm(vb)) + 1e-9))


def context_recall(contexts: list[str], expected_keywords: list[str]) -> float:
    """Fraction of expected keywords found anywhere in the retrieved contexts."""
    if not expected_keywords:
        return 0.0
    joined = "\n".join(contexts).lower()
    found = sum(1 for kw in expected_keywords if kw.lower() in joined)
    return found / len(expected_keywords)


def context_precision(contexts: list[str], expected_keywords: list[str]) -> float:
    """Fraction of retrieved chunks that contain at least one expected keyword."""
    if not contexts:
        return 0.0
    keywords = [kw.lower() for kw in expected_keywords]
    relevant = sum(1 for c in contexts if any(kw in c.lower() for kw in keywords))
    return relevant / len(contexts)


def faithfulness(answer: str, contexts: list[str]) -> float:
    """LLM-judged support of the answer by the context (0..1)."""
    prompt = _FAITHFULNESS_PROMPT.format(context="\n\n".join(contexts), answer=answer)
    try:
        match = re.search(r"[01](?:\.\d+)?", generate(prompt))
        return max(0.0, min(1.0, float(match.group()))) if match else 0.0
    except Exception:
        return 0.0


def answer_relevancy(question: str, answer: str) -> float:
    embeddings = get_embeddings()
    return _cosine(embeddings.embed_query(question), embeddings.embed_query(answer))


def answer_correctness(answer: str, reference_answer: str) -> float:
    embeddings = get_embeddings()
    return _cosine(embeddings.embed_query(answer), embeddings.embed_query(reference_answer))
