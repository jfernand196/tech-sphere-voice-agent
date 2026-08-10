"""Unit tests for VoiceService — fake TtsEnginePort, no model downloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pytest

from app.config import Settings
from app.voice.service import VoiceService


@dataclass
class FakeTtsEngine:
    """In-memory TtsEnginePort for routing / capabilities tests."""

    label: str
    ready: bool = True
    voices: List[dict] = field(default_factory=list)
    default_voice: str = "fake"
    calls: List[Tuple[str, Optional[str], Optional[float]]] = field(default_factory=list)

    def available(self) -> bool:
        return self.ready

    def list_voices(self) -> List[dict]:
        return list(self.voices)

    def status(self) -> dict:
        return {
            "files_present": self.ready,
            "loaded": False,
            "default_voice": self.default_voice,
            "error": None,
            "voices": self.list_voices(),
        }

    def warmup(self) -> None:
        return None

    def synthesize(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> Tuple[bytes, str]:
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("text is empty")
        self.calls.append((cleaned, voice, speed))
        return f"WAV:{self.label}:{cleaned}".encode(), "audio/wav"


def _service(
    *,
    tts_provider: str = "auto",
    kokoro_ready: bool = True,
    piper_ready: bool = True,
    piper_speed: float = 1.1,
) -> tuple[VoiceService, FakeTtsEngine, FakeTtsEngine]:
    settings = Settings(tts_provider=tts_provider, piper_speed=piper_speed)
    kokoro = FakeTtsEngine(
        "kokoro",
        ready=kokoro_ready,
        voices=[{"id": "ef_dora", "label": "Dora"}],
        default_voice="ef_dora",
    )
    piper = FakeTtsEngine(
        "piper",
        ready=piper_ready,
        voices=[{"id": "es_MX-ald-medium", "label": "Ald"}],
        default_voice="es_MX-ald-medium",
    )
    return (
        VoiceService(settings=settings, kokoro=kokoro, piper=piper),
        kokoro,
        piper,
    )


def test_capabilities_only_engines_namespace() -> None:
    svc, _, _ = _service(kokoro_ready=False, piper_ready=True)
    caps = svc.capabilities()

    assert set(caps["engines"]) == {"browser", "kokoro", "piper"}
    assert caps["engines"]["browser"]["available"] is True
    assert caps["engines"]["kokoro"]["available"] is False
    assert caps["engines"]["piper"]["available"] is True
    assert caps["engines"]["piper"]["voices"][0]["id"] == "es_MX-ald-medium"
    assert "mode" not in caps
    assert "kokoro" not in caps
    assert "piper" not in caps


def test_browser_provider_disables_server_engines() -> None:
    svc, _, _ = _service(tts_provider="browser")
    assert svc.engine_available("kokoro") is False
    assert svc.engine_available("piper") is False
    caps = svc.capabilities()
    assert caps["engines"]["kokoro"]["available"] is False
    assert caps["engines"]["piper"]["available"] is False


def test_piper_provider_hides_kokoro() -> None:
    svc, _, _ = _service(tts_provider="piper")
    assert svc.kokoro_available() is False
    assert svc.piper_available() is True


def test_auto_prefers_kokoro_when_both_ready() -> None:
    svc, kokoro, piper = _service()
    audio, ctype = svc.synthesize_tts("Hola")
    assert ctype == "audio/wav"
    assert audio.startswith(b"WAV:kokoro:")
    assert len(kokoro.calls) == 1
    assert piper.calls == []


def test_explicit_piper_routes_to_piper() -> None:
    svc, kokoro, piper = _service()
    audio, _ = svc.synthesize_tts("Hola", engine="piper", voice="es_MX-ald-medium")
    assert audio.startswith(b"WAV:piper:")
    assert kokoro.calls == []
    assert len(piper.calls) == 1
    text, voice, speed = piper.calls[0]
    assert text == "Hola"
    assert voice == "es_MX-ald-medium"
    assert speed == 1.1


def test_auto_falls_back_to_piper_when_kokoro_missing() -> None:
    svc, kokoro, piper = _service(kokoro_ready=False, piper_ready=True)
    audio, _ = svc.synthesize_tts("Hola")
    assert audio.startswith(b"WAV:piper:")
    assert kokoro.calls == []
    assert len(piper.calls) == 1


def test_no_server_engine_raises() -> None:
    svc, _, _ = _service(kokoro_ready=False, piper_ready=False)
    with pytest.raises(RuntimeError, match="Server TTS is not active"):
        svc.synthesize_tts("Hola")


def test_unsupported_engine_raises() -> None:
    svc, _, _ = _service()
    with pytest.raises(RuntimeError, match="Unsupported TTS engine"):
        svc.synthesize_tts("Hola", engine="elevenlabs")


def test_explicit_piper_unavailable_raises() -> None:
    svc, _, _ = _service(piper_ready=False)
    with pytest.raises(RuntimeError, match="Piper TTS is not active"):
        svc.synthesize_tts("Hola", engine="piper")


def test_empty_text_propagates_value_error() -> None:
    svc, _, _ = _service()
    with pytest.raises(ValueError, match="empty"):
        svc.synthesize_tts("   ", engine="kokoro")
