"""Hybrid BM25 + embedding-cosine retrieval (hash by default in unit tests)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.rag.embeddings import HashEmbedder
from app.rag.store import LocalVectorStore, bm25_scores, rrf_fuse


def test_bm25_prefers_rare_term_match() -> None:
    docs = [
        ["cuidado", "herida", "limpia"],
        ["protocolo", "zeta42", "lavar", "herida"],
        ["dolor", "leve", "reposo"],
    ]
    scores = bm25_scores(["zeta42", "protocolo"], docs)
    assert scores[1] == max(scores)


def test_rrf_fuse_boosts_agreement() -> None:
    # Doc 1 is #1 in both rankings → highest fused score.
    fused = rrf_fuse([1, 0, 2], [1, 2, 0])
    assert max(fused, key=fused.get) == 1


def test_hybrid_search_finds_unique_protocol(tmp_path: Path) -> None:
    store = LocalVectorStore(
        tmp_path / "docs.json",
        tmp_path / "vectors",
        embedder=HashEmbedder(),
    )
    store.add_document(
        title="Cuidados generales",
        filename="a.txt",
        text="Mantener la herida limpia y seca. Caminar según indicación médica.",
    )
    store.add_document(
        title="Protocolo ZETA-42",
        filename="b.txt",
        text=(
            "Protocolo ZETA-42: lavar la herida con solución X dos veces al día. "
            "No aplica a otros protocolos del hospital."
        ),
    )
    store.add_document(
        title="Dieta",
        filename="c.txt",
        text="Dieta blanda los primeros días. Hidratación abundante.",
    )

    hits = store.search("¿Qué dice el protocolo ZETA-42?", top_k=2)
    assert hits
    assert hits[0][0].title == "Protocolo ZETA-42"
    assert "ZETA-42" in hits[0][0].text or "zeta" in hits[0][0].text.lower()


def test_hybrid_search_clinical_keywords(tmp_path: Path) -> None:
    store = LocalVectorStore(
        tmp_path / "docs.json",
        tmp_path / "vectors",
        embedder=HashEmbedder(),
    )
    store.add_document(
        title="Alarma infección",
        filename="inf.txt",
        text=(
            "Signos de alarma: secreción purulenta, fiebre mayor a 38.5, "
            "eritema creciente alrededor de la herida."
        ),
    )
    store.add_document(
        title="Reposo",
        filename="rest.txt",
        text="Reposo relativo y caminatas cortas en casa.",
    )

    hits = store.search("tengo fiebre y secreción purulenta en la herida", top_k=1)
    assert hits
    assert hits[0][0].title == "Alarma infección"


def test_dim_mismatch_marks_reembed(tmp_path: Path) -> None:
    store = LocalVectorStore(
        tmp_path / "docs.json",
        tmp_path / "vectors",
        embedder=HashEmbedder(),
    )
    store.add_document(
        title="Protocolo",
        filename="p.txt",
        text="Dolor abdominal postoperatorio y fiebre leve.",
        metadata={"path": str(tmp_path / "p.txt")},
    )
    assert store._chunks
    assert len(store._chunks[0].embedding) == 256

    # Simulate load with a different embedder dim (384).
    class _Fake384:
        name = "fake384"
        dim = 384

        def embed_query(self, text: str):
            return [0.0] * 384

        def embed_documents(self, texts):
            return [[0.0] * 384 for _ in texts]

        def warmup(self) -> None:
            return None

    store2 = LocalVectorStore(
        tmp_path / "docs.json",
        tmp_path / "vectors",
        embedder=_Fake384(),
    )
    assert store2.needs_reembed is True
    assert store2._chunks == []
    assert store2.list_documents()  # catalog preserved


def test_empty_chunks_with_catalog_marks_reembed(tmp_path: Path) -> None:
    """Catalog without vectors must rebuild (not stay stuck empty forever)."""
    docs_path = tmp_path / "docs.json"
    vec_dir = tmp_path / "vectors"
    vec_dir.mkdir()
    docs_path.write_text(
        json.dumps(
            [
                {
                    "doc_id": "d1",
                    "title": "Herida",
                    "filename": "h.txt",
                    "chunk_count": 3,
                    "created_at": "2026-01-01T00:00:00",
                    "metadata": {"path": str(tmp_path / "h.txt")},
                }
            ]
        ),
        encoding="utf-8",
    )
    (vec_dir / "chunks.json").write_text("[]", encoding="utf-8")
    (vec_dir / "embed_meta.json").write_text(
        json.dumps({"provider": "hash", "dim": 256}),
        encoding="utf-8",
    )

    store = LocalVectorStore(docs_path, vec_dir, embedder=HashEmbedder())
    assert store.needs_reembed is True
    assert store._chunks == []
    assert store.list_documents()


@pytest.mark.slow
def test_fastembed_indexes_and_retrieves(tmp_path: Path) -> None:
    """Semantic smoke: synonym query should still hit the clinical chunk."""
    from app.rag.embeddings import FastembedEmbedder

    store = LocalVectorStore(
        tmp_path / "docs.json",
        tmp_path / "vectors",
        embedder=FastembedEmbedder(),
    )
    store.add_document(
        title="Síntomas abdominales",
        filename="abd.txt",
        text=(
            "El dolor abdominal postoperatorio puede ser normal si es leve. "
            "Malestar intenso con fiebre requiere evaluación."
        ),
    )
    store.add_document(
        title="Cuidado de pies",
        filename="pies.txt",
        text="Mantener los pies elevados y usar medias de compresión según indicación.",
    )

    hits = store.search("malestar en el abdomen", top_k=1)
    assert hits
    assert hits[0][0].title == "Síntomas abdominales"
    assert "abdominal" in hits[0][0].text.lower() or "abdomen" in hits[0][0].text.lower()
