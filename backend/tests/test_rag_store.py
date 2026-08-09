"""Hybrid BM25 + hash-cosine retrieval."""

from __future__ import annotations

from pathlib import Path

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
    store = LocalVectorStore(tmp_path / "docs.json", tmp_path / "vectors")
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
    store = LocalVectorStore(tmp_path / "docs.json", tmp_path / "vectors")
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
