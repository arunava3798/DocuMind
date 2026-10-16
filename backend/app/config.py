"""Application settings loaded from environment / .env (env-driven provider switches)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "RAG Platform API"

    # LLM provider: "gemini" | "ollama"
    llm_backend: str = "gemini"
    gemini_model: str = "gemini-flash-lite-latest"
    ollama_model: str = "llama3.2"
    ollama_url: str = "http://localhost:11434/api/generate"
    google_api_key: str | None = None

    # Embedding provider: "local" (sentence-transformers) | "api" (Gemini)
    embedding_backend: str = "local"
    embedding_model_local: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_model_api: str = "gemini-embedding-001"

    # Retrieval / chunking
    chunk_size: int = 1000
    chunk_overlap: int = 150
    top_k: int = 4

    # Retrieval quality (Phase 3)
    retrieval_mode: str = "hybrid"  # dense | hybrid
    retrieval_candidates: int = 20  # candidates fetched before re-ranking
    rerank_enabled: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    multi_query_enabled: bool = True
    num_queries: int = 3  # original + (n-1) LLM-generated variants

    # Storage
    index_dir: str = "index"

    # Database (Postgres + pgvector). Example (Neon):
    # postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require
    database_url: str | None = None
    pg_collection_name: str = "rag_documents"

    # Observability
    log_level: str = "INFO"
    log_json: bool = True
    # Estimated Gemini pricing (USD per 1M tokens) for cost reporting only.
    gemini_input_cost_per_mtok: float = 0.10
    gemini_output_cost_per_mtok: float = 0.40

    # CORS (Angular dev server by default)
    cors_origins: list[str] = ["http://localhost:4200"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
