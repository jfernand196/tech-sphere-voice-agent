"""Kokoro TTS wiring (slow path needs model files from make warm-kokoro)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_voice_capabilities_shape(client: TestClient) -> None:
    res = client.get("/voice/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert "mode" in body
    assert "kokoro" in body
    assert "voices" in body["kokoro"]


@pytest.mark.slow
def test_kokoro_tts_returns_wav(client: TestClient) -> None:
    settings = get_settings()
    if not settings.kokoro_model_path.is_file():
        pytest.skip("Kokoro model not downloaded; run make warm-kokoro")
    res = client.post(
        "/voice/tts",
        json={"text": "Hola, ¿cómo se siente la herida?", "voice": "ef_dora"},
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/")
    assert res.content[:4] == b"RIFF"
