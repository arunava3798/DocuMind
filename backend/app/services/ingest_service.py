"""Ingestion service: accept uploads, extract, chunk, index in pgvector, record metadata."""
from __future__ import annotations

import os
import tempfile
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..core import vectorstore
from ..core.chunker import chunk_documents
from ..core.loader import SUPPORTED_EXTENSIONS, load_file
from ..db.models import Document


async def ingest_files(files: list[UploadFile], db: Session) -> list[Document]:
    """Process each uploaded file into pgvector and a `documents` row."""
    created: list[Document] = []
    for upload in files:
        ext = os.path.splitext(upload.filename or "")[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        data = await upload.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            docs = load_file(tmp_path)
        finally:
            os.unlink(tmp_path)

        doc_id = uuid.uuid4()
        for doc in docs:
            doc.metadata["source"] = upload.filename
            doc.metadata["document_id"] = str(doc_id)

        chunks = chunk_documents(docs)
        if not chunks:
            continue

        chunk_ids = [str(uuid.uuid4()) for _ in chunks]
        for chunk, chunk_id in zip(chunks, chunk_ids):
            chunk.metadata["chunk_id"] = chunk_id
        vectorstore.add_documents(chunks, ids=chunk_ids)

        record = Document(
            id=doc_id,
            filename=upload.filename,
            content_type=upload.content_type,
            size_bytes=len(data),
            chunk_count=len(chunks),
            chunk_ids=chunk_ids,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        created.append(record)

    return created
