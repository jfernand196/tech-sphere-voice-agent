"""Application ports (DIP): concrete adapters depend on these contracts."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Protocol

from app.schemas import DocumentInfo, KnowledgeChunk


class KnowledgePort(Protocol):
    def list_documents(self) -> List[DocumentInfo]: ...

    def ingest_text(
        self,
        *,
        title: str,
        filename: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> DocumentInfo: ...

    def ingest_upload(self, *, title: str, filename: str, content: bytes) -> DocumentInfo: ...

    def delete(self, doc_id: str) -> bool: ...

    def retrieve(self, query: str, top_k: int = 4) -> List[KnowledgeChunk]: ...


class LLMClient(Protocol):
    """Generates a structured agent payload from conversation + RAG context."""

    model_id: str

    async def complete(
        self,
        *,
        patient_name: str,
        procedure: str,
        dia_postop: int,
        message: str,
        history: List[Dict[str, str]],
        rag_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]: ...
