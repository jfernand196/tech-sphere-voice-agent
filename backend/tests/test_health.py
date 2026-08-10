""" /health includes LLM + RAG index readiness. """

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_exposes_rag_index_fields() -> None:
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert "status" in body
    assert "llm_ready" in body
    assert "rag_ok" in body
    assert "rag_docs" in body
    assert "rag_chunks" in body
    assert "rag_embedder" in body
    # Docs without vectors must not report a healthy index.
    if body["rag_docs"] > 0 and body["rag_chunks"] == 0:
        assert body["rag_ok"] is False
        assert body["status"] == "degraded"
    if body["rag_docs"] > 0 and body["rag_chunks"] > 0:
        assert body["rag_ok"] is True
