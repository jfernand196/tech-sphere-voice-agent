from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.config import Settings
from app.rag.store import LocalVectorStore
from app.schemas import DocumentInfo, KnowledgeChunk


class KnowledgeService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = LocalVectorStore(
            data_dir=settings.data_dir,
            documents_path=settings.documents_path,
            vector_dir=settings.vector_store_dir,
        )

    def list_documents(self) -> list[DocumentInfo]:
        return [
            DocumentInfo(
                doc_id=d.doc_id,
                title=d.title,
                filename=d.filename,
                chunk_count=d.chunk_count,
                created_at=d.created_at,
                metadata=d.metadata,
            )
            for d in self.store.list_documents()
        ]

    def ingest_text(
        self,
        *,
        title: str,
        filename: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> DocumentInfo:
        record = self.store.add_document(
            title=title,
            filename=filename,
            text=text,
            metadata=metadata,
        )
        return DocumentInfo(
            doc_id=record.doc_id,
            title=record.title,
            filename=record.filename,
            chunk_count=record.chunk_count,
            created_at=record.created_at,
            metadata=record.metadata,
        )

    def ingest_upload(self, *, title: str, filename: str, content: bytes) -> DocumentInfo:
        text = content.decode("utf-8", errors="ignore")
        dest = self.settings.uploads_dir / filename
        # Avoid overwrite collisions
        if dest.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            dest = self.settings.uploads_dir / f"{stem}-{Path(dest).stat().st_mtime_ns}{suffix}"
        dest.write_bytes(content)
        return self.ingest_text(
            title=title or Path(filename).stem,
            filename=dest.name,
            text=text,
            metadata={"path": str(dest)},
        )

    def delete(self, doc_id: str) -> bool:
        doc = self.store.get_document(doc_id)
        if not doc:
            return False
        path = doc.metadata.get("path")
        if path:
            p = Path(path)
            if p.exists():
                p.unlink()
        return self.store.delete_document(doc_id)

    def retrieve(self, query: str, top_k: int = 4) -> list[KnowledgeChunk]:
        hits = self.store.search(query, top_k=top_k)
        return [
            KnowledgeChunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                title=chunk.title,
                text=chunk.text,
                score=round(score, 4),
            )
            for chunk, score in hits
        ]
