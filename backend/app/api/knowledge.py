from __future__ import annotations

from typing import List

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api.deps import get_knowledge_service
from app.schemas import DocumentInfo, KnowledgeChunk, KnowledgeQueryRequest

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.get("/documents", response_model=List[DocumentInfo])
def list_documents():
    return get_knowledge_service().list_documents()


@router.post("/documents", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(""),
):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    return get_knowledge_service().ingest_upload(
        title=title or (file.filename or "documento"),
        filename=file.filename or "documento.txt",
        content=content,
    )


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: str):
    ok = get_knowledge_service().delete(doc_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"deleted": True, "doc_id": doc_id}


@router.post("/query", response_model=List[KnowledgeChunk])
def query_knowledge(body: KnowledgeQueryRequest):
    return get_knowledge_service().retrieve(body.query, top_k=body.top_k)
