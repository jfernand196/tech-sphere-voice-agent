"""Server TTS wiring (Kokoro / Piper; slow paths need warm-* downloads)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.voice.service import VoiceService


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_voice_capabilities_shape(client: TestClient) -> None:
    res = client.get("/voice/capabilities")
    assert res.status_code == 200
    body = res.json()
    assert "engines" in body
    assert "browser" in body["engines"]
    assert "kokoro" in body["engines"]
    assert "piper" in body["engines"]
    assert "available" in body["engines"]["kokoro"]
    assert "voices" in body["engines"]["kokoro"]
    assert "voices" in body["engines"]["piper"]
    # No legacy single-mode / duplicated top-level engine blobs.
    assert "mode" not in body
    assert "kokoro" not in body
    assert "piper" not in body


def test_transcribe_endpoint_removed(client: TestClient) -> None:
    res = client.post("/voice/transcribe", files={"file": ("a.webm", b"x", "audio/webm")})
    assert res.status_code in {404, 405}


def test_tts_rejects_empty_text(client: TestClient) -> None:
    res = client.post("/voice/tts", json={"text": ""})
    assert res.status_code == 422


@pytest.mark.slow
def test_kokoro_tts_returns_wav(client: TestClient) -> None:
    settings = get_settings()
    if not settings.kokoro_model_path.is_file():
        pytest.skip("Kokoro model not downloaded; run make warm-kokoro")
    res = client.post(
        "/voice/tts",
        json={
            "text": "Hola, ¿cómo se siente la herida?",
            "engine": "kokoro",
            "voice": "ef_dora",
        },
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/")
    assert res.content[:4] == b"RIFF"


@pytest.mark.slow
def test_piper_tts_returns_wav(client: TestClient) -> None:
    service = VoiceService()
    if not service.piper_available():
        pytest.skip("Piper voices not downloaded; run make warm-piper")
    res = client.post(
        "/voice/tts",
        json={
            "text": "Hola, ¿cómo se siente la herida?",
            "engine": "piper",
            "voice": "es_MX-ald-medium",
        },
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("audio/")
    assert res.content[:4] == b"RIFF"
