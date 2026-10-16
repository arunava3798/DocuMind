"""Embedding provider switch: local sentence-transformers or Gemini embedding API."""
from __future__ import annotations

from functools import lru_cache

import requests
from langchain_core.embeddings import Embeddings

from ..config import get_settings

_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent"


class GeminiAPIEmbeddings(Embeddings):
    """Embeddings backed by Gemini's free embedContent endpoint (keeps the app torch-free)."""

    def __init__(self, model: str, api_key: str) -> None:
        self.model = model
        self.api_key = api_key
        self.url = _API_URL.format(model=model)

    def _embed(self, text: str) -> list[float]:
        response = requests.post(
            self.url,
            params={"key": self.api_key},
            json={"content": {"parts": [{"text": text}]}},
            timeout=60,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Embedding API error {response.status_code}: {response.text}")
        return response.json()["embedding"]["values"]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


@lru_cache
def get_embeddings() -> Embeddings:
    settings = get_settings()
    if settings.embedding_backend == "api":
        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is required when EMBEDDING_BACKEND=api.")
        return GeminiAPIEmbeddings(settings.embedding_model_api, settings.google_api_key)

    from langchain_huggingface import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model_local,
        encode_kwargs={"normalize_embeddings": True},
    )
