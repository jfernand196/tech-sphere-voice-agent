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
            sources_dir=settings.sources_dir,
        )

    @property
    def needs_reembed(self) -> bool:
        return self.store.needs_reembed

    def index_stats(self) -> dict:
        return self.store.index_stats()

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

    def _read_source_file(self, path: Path) -> Optional[str]:
        if not path.is_file():
            return None
        try:
            if path.suffix.lower() in {".txt", ".md", ""}:
                text = path.read_text(encoding="utf-8")
            else:
                text = extract_text(path.name, path.read_bytes())
        except Exception:
            return None
        return text if len(text.strip()) >= 20 else None

    def resolve_source_text(self, doc: DocumentRecord) -> Optional[str]:
        """Prefer upload path, then snapshot, then in-memory chunks."""
        meta = doc.metadata or {}
        for key in ("path", "source_path"):
            raw = meta.get(key)
            if not raw:
                continue
            text = self._read_source_file(Path(raw))
            if text:
                return text
        # Snapshot by doc_id even if metadata lost the pointer.
        text = self._read_source_file(self.store.source_file(doc.doc_id))
        if text:
            return text
        parts = [c.text for c in self.store.chunks_for(doc.doc_id)]
        if parts:
            joined = "\n\n".join(parts)
            return joined if len(joined.strip()) >= 20 else None
        return None

    def _doc_needs_rebuild(self, doc: DocumentRecord) -> bool:
        if doc.chunk_count == 0:
            return True
        for chunk in self.store.chunks_for(doc.doc_id):
            return len(chunk.embedding) != self.embedder.dim
        return True

    def rebuild_stale_embeddings(self) -> int:
        """Re-embed docs from path/snapshot; resume-safe across restarts."""
        pending = [d for d in self.store.list_documents() if self._doc_needs_rebuild(d)]
        if not self.store.needs_reembed and not pending:
            return 0

        # Safety net if wipe left chunks that still need archiving.
        if self.store._chunks:
            self.store.archive_sources_from_chunks()
            self.store._persist()

        rebuilt = 0
        for doc in list(self.store.list_documents()):
            if not self._doc_needs_rebuild(doc):
                continue
            text = self.resolve_source_text(doc)
            if not text:
                print(
                    f"[rag] skip rebuild (no source text): "
                    f"{doc.doc_id} · {doc.title!r}"
                )
                continue
            meta = dict(doc.metadata or {})
            title = doc.title
            filename = doc.filename
            self.store.delete_document(doc.doc_id)
            self.ingest_text(
                title=title,
                filename=filename,
                text=text,
                metadata=meta,
            )
            rebuilt += 1

        still_pending = [
            d for d in self.store.list_documents() if self._doc_needs_rebuild(d)
        ]
        self.store.needs_reembed = bool(still_pending)
        if still_pending:
            print(
                f"[rag] rebuild incomplete: {len(still_pending)} doc(s) still pending "
                "(will retry on next startup)"
            )
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
