"""Simple local vector store (hash embeddings). Swap for pgvector/Chroma later."""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ChunkRecord:
    chunk_id: str
    doc_id: str
    title: str
    text: str
    embedding: List[float]


@dataclass
class DocumentRecord:
    doc_id: str
    title: str
    filename: str
    chunk_count: int
    created_at: str
    metadata: dict


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-záéíóúñü0-9]+", text.lower())


def embed_text(text: str, dims: int = 256) -> List[float]:
    """Deterministic bag-of-tokens embedding (no external model required)."""
    vec = [0.0] * dims
    tokens = _tokenize(text)
    if not tokens:
        return vec
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dims
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    denom = na * nb
    if denom == 0:
        return 0.0
    return dot / denom


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """Prefer paragraph/sentence boundaries so excerpts don't start mid-phrase."""
    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", normalized)]
    paragraphs = [p for p in paragraphs if p]
    units: List[str] = []
    for para in paragraphs or [re.sub(r"\s+", " ", normalized)]:
        sentences = re.split(r"(?<=[.!?:;])\s+(?=[A-ZÁÉÍÓÚ¿¡-]|\d)", para)
        buf = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            candidate = f"{buf} {sentence}".strip() if buf else sentence
            if len(candidate) <= chunk_size:
                buf = candidate
            else:
                if buf:
                    units.append(buf)
                if len(sentence) <= chunk_size:
                    buf = sentence
                else:
                    # Hard wrap very long sentences as a last resort.
                    start = 0
                    while start < len(sentence):
                        units.append(sentence[start : start + chunk_size])
                        start += max(1, chunk_size - overlap)
                    buf = ""
        if buf:
            units.append(buf)
    return units


class LocalVectorStore:
    def __init__(self, documents_path: Path, vector_dir: Path) -> None:
        self.documents_path = documents_path
        self.chunks_path = vector_dir / "chunks.json"
        self._documents: Dict[str, DocumentRecord] = {}
        self._chunks: List[ChunkRecord] = []
        self._load()

    def _load(self) -> None:
        if self.documents_path.exists():
            raw = json.loads(self.documents_path.read_text(encoding="utf-8"))
            self._documents = {d["doc_id"]: DocumentRecord(**d) for d in raw}
        if self.chunks_path.exists():
            raw_chunks = json.loads(self.chunks_path.read_text(encoding="utf-8"))
            self._chunks = [ChunkRecord(**c) for c in raw_chunks]

    def _persist(self) -> None:
        self.documents_path.write_text(
            json.dumps([asdict(d) for d in self._documents.values()], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.chunks_path.write_text(
            json.dumps([asdict(c) for c in self._chunks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_documents(self) -> List[DocumentRecord]:
        return sorted(self._documents.values(), key=lambda d: d.created_at, reverse=True)

    def get_document(self, doc_id: str) -> Optional[DocumentRecord]:
        return self._documents.get(doc_id)

    def add_document(
        self,
        *,
        title: str,
        filename: str,
        text: str,
        metadata: Optional[dict] = None,
    ) -> DocumentRecord:
        doc_id = str(uuid.uuid4())
        parts = chunk_text(text)
        new_chunks: List[ChunkRecord] = []
        for idx, part in enumerate(parts):
            new_chunks.append(
                ChunkRecord(
                    chunk_id=f"{doc_id}:{idx}",
                    doc_id=doc_id,
                    title=title,
                    text=part,
                    embedding=embed_text(part),
                )
            )
        record = DocumentRecord(
            doc_id=doc_id,
            title=title,
            filename=filename,
            chunk_count=len(new_chunks),
            created_at=_utcnow().isoformat(),
            metadata=metadata or {},
        )
        self._documents[doc_id] = record
        self._chunks.extend(new_chunks)
        self._persist()
        return record

    def delete_document(self, doc_id: str) -> bool:
        if doc_id not in self._documents:
            return False
        del self._documents[doc_id]
        self._chunks = [c for c in self._chunks if c.doc_id != doc_id]
        self._persist()
        return True

    def search(self, query: str, top_k: int = 4) -> List[Tuple[ChunkRecord, float]]:
        if not self._chunks:
            return []
        q = embed_text(query)
        scored = [(chunk, cosine(q, chunk.embedding)) for chunk in self._chunks]
        scored.sort(key=lambda item: item[1], reverse=True)
        filtered = [(c, s) for c, s in scored if s > 0.05]
        return filtered[:top_k]
