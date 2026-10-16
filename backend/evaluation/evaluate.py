"""Run the evaluation: ingest the sample doc, answer the golden questions, score them.

Usage (from backend/):  python -m evaluation.evaluate
Requires DATABASE_URL and GOOGLE_API_KEY in backend/.env.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import retriever
from app.main import app
from evaluation import metrics

DATASET = Path(__file__).parent / "dataset.json"
SAMPLE_DOC = Path(__file__).resolve().parents[2] / "data" / "sample_project_nimbus.txt"
METRIC_NAMES = [
    "context_recall",
    "context_precision",
    "faithfulness",
    "answer_relevancy",
    "answer_correctness",
]


def _ingest(client: TestClient) -> None:
    with open(SAMPLE_DOC, "rb") as f:
        client.post("/api/documents/ingest", files=[("files", (SAMPLE_DOC.name, f, "text/plain"))])


def _cleanup(client: TestClient) -> None:
    for doc in client.get("/api/documents").json():
        client.delete(f"/api/documents/{doc['id']}")


def run() -> None:
    examples = json.loads(DATASET.read_text(encoding="utf-8"))
    totals = {name: 0.0 for name in METRIC_NAMES}

    with TestClient(app) as client:
        _ingest(client)
        print(f"\nEvaluating {len(examples)} questions...\n")
        header = f"{'question':50} " + " ".join(f"{n[:12]:>12}" for n in METRIC_NAMES)
        print(header)
        print("-" * len(header))

        for ex in examples:
            resp = client.post("/api/chat", json={"question": ex["question"]}).json()
            answer = resp["answer"]
            # Use the full retrieved chunks (not the 500-char display snippets) for context metrics.
            contexts = [doc.page_content for doc in retriever.retrieve(ex["question"])]

            scores = {
                "context_recall": metrics.context_recall(contexts, ex["expected_keywords"]),
                "context_precision": metrics.context_precision(contexts, ex["expected_keywords"]),
                "faithfulness": metrics.faithfulness(answer, contexts),
                "answer_relevancy": metrics.answer_relevancy(ex["question"], answer),
                "answer_correctness": metrics.answer_correctness(answer, ex["reference_answer"]),
            }
            for name, value in scores.items():
                totals[name] += value

            row = f"{ex['question'][:50]:50} " + " ".join(f"{scores[n]:>12.3f}" for n in METRIC_NAMES)
            print(row)

        _cleanup(client)

    n = len(examples)
    print("-" * len(header))
    print(f"{'AVERAGE':50} " + " ".join(f"{totals[name] / n:>12.3f}" for name in METRIC_NAMES))
    print()


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL") and not os.getenv("GOOGLE_API_KEY"):
        from dotenv import load_dotenv

        load_dotenv()
    run()
