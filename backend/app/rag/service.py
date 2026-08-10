from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.config import Settings
from app.rag.embeddings import Embedder, get_embedder
from app.rag.extract import extract_text
from app.rag.store import DocumentRecord, LocalVectorStore
from app.schemas import DocumentInfo, KnowledgeChunk


class KnowledgeService:
    def __init__(
        self,
        settings: Settings,
        embedder: Optional[Embedder] = None,
    ) -> None:
        self.settings = settings
        self.embedder = embedder or get_embedder(settings.embed_provider)
        self.store = LocalVectorStore(
            documents_path=settings.documents_path,
            vector_dir=settings.vector_store_dir,
            embedder=self.embedder,
        )

    @property
    def needs_reembed(self) -> bool:
        return self.store.needs_reembed

    def list_documents(self) -> list[DocumentInfo]:
        return [self._to_info(d) for d in self.store.list_documents()]

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
        return self._to_info(record)

    def ingest_upload(self, *, title: str, filename: str, content: bytes) -> DocumentInfo:
        text = extract_text(filename, content)
        if len(text.strip()) < 20:
            raise ValueError(
                f"No se pudo extraer texto útil de '{filename}'. "
                "Usa PDF con texto seleccionable, o .txt/.md."
            )
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
            metadata={"path": str(dest), "content_type": Path(filename).suffix.lower()},
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

    def rebuild_stale_embeddings(self) -> int:
        """Re-ingest docs from metadata['path'] after embedder dim/provider change."""
        if not self.store.needs_reembed:
            return 0

        docs = list(self.store.list_documents())
        rebuilt = 0
        for doc in docs:
            path_raw = (doc.metadata or {}).get("path")
            path = Path(path_raw) if path_raw else None
            if path is None or not path.exists():
                # Drop catalog-only rows (e.g. old seed without a file).
                self.store.delete_document(doc.doc_id)
                continue
            try:
                content = path.read_bytes()
                text = extract_text(path.name, content)
            except Exception:
                self.store.delete_document(doc.doc_id)
                continue
            if len(text.strip()) < 20:
                self.store.delete_document(doc.doc_id)
                continue
            meta = dict(doc.metadata or {})
            meta["path"] = str(path)
            self.store.delete_document(doc.doc_id)
            self.ingest_text(
                title=doc.title,
                filename=doc.filename,
                text=text,
                metadata=meta,
            )
            rebuilt += 1

        self.store.needs_reembed = False
        return rebuilt

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

    @staticmethod
    def _to_info(record: DocumentRecord) -> DocumentInfo:
        return DocumentInfo(
            doc_id=record.doc_id,
            title=record.title,
            filename=record.filename,
            chunk_count=record.chunk_count,
            created_at=record.created_at,
            metadata=record.metadata,
        )
