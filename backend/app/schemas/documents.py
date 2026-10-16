"""Document ingestion schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    chunk_count: int
    size_bytes: int
    created_at: datetime


class IngestResponse(BaseModel):
    ingested_files: list[str]
    total_chunks: int
    documents: list[DocumentInfo]

