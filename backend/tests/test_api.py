"""Integration tests for the API (skipped unless DATABASE_URL and GOOGLE_API_KEY are set)."""
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

SAMPLE_DOC = Path(__file__).resolve().parents[2] / "data" / "sample_project_nimbus.txt"

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("GOOGLE_API_KEY"),
    reason="integration env (DATABASE_URL / GOOGLE_API_KEY) not configured",
)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_ingest_chat_delete_flow(client):
    with open(SAMPLE_DOC, "rb") as f:
        ingest = client.post(
            "/api/documents/ingest",
            files=[("files", ("nimbus.txt", f, "text/plain"))],
        )
    assert ingest.status_code == 200
    assert ingest.json()["total_chunks"] > 0

    chat = client.post("/api/chat", json={"question": "How much does the Pro plan cost?"})
    assert chat.status_code == 200
    assert "8" in chat.json()["answer"]
    assert chat.json()["sources"]

    docs = client.get("/api/documents").json()
    assert len(docs) >= 1
    for doc in docs:
        assert client.delete(f"/api/documents/{doc['id']}").status_code == 204
    assert client.get("/api/documents").json() == []
