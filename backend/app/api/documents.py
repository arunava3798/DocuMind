"""Document endpoints: ingest, list, and delete documents."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core import vectorstore
from ..db.database import get_session
from ..db.models import Document
from ..schemas.documents import DocumentInfo, IngestResponse
from ..services import ingest_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_session),
) -> IngestResponse:
    created = await ingest_service.ingest_files(files, db)
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return IngestResponse(
        ingested_files=[d.filename for d in created],
        total_chunks=sum(d.chunk_count for d in created),
        documents=[DocumentInfo.model_validate(d) for d in documents],
    )


@router.get("", response_model=list[DocumentInfo])
def list_documents(db: Session = Depends(get_session)) -> list[DocumentInfo]:
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [DocumentInfo.model_validate(d) for d in documents]


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID, db: Session = Depends(get_session)) -> None:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    vectorstore.delete_ids(document.chunk_ids or [])
    db.delete(document)
    db.commit()

