"""Voice adapters: browser STT + Kokoro (or browser) TTS."""

from __future__ import annotations

from typing import Optional

from app.config import Settings, get_settings
from app.voice.kokoro_engine import get_kokoro_engine


class VoiceService:
    def __init__(self, settings: Optional[Settings] = None) -> None:
        self.settings = settings or get_settings()
        self.kokoro = get_kokoro_engine()

    def capabilities(self) -> dict:
        provider = self.settings.tts_provider.strip().lower()
        kokoro = self.kokoro.status()
        effective = "browser"
        if provider == "kokoro" and kokoro["files_present"]:
            effective = "kokoro"
        elif provider == "auto" and kokoro["files_present"]:
            effective = "kokoro"
        elif provider == "browser":
            effective = "browser"

        return {
            "mode": effective,
            "stt": "browser-web-speech-api (client)",
            "tts": (
                "kokoro-onnx (server WAV)"
                if effective == "kokoro"
                else "browser-speechSynthesis (client)"
            ),
            "tts_provider_setting": provider,
            "kokoro": kokoro,
            "telephony": False,
            "note": "No real telephony required for the challenge.",
        }

    def synthesize_tts(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> tuple[bytes, str]:
        caps = self.capabilities()
        if caps["mode"] != "kokoro":
            raise RuntimeError(
                "Kokoro TTS is not active. Set TTS_PROVIDER=kokoro|auto and run make warm-kokoro."
            )
        return self.kokoro.synthesize(text, voice=voice, speed=speed)

    async def transcribe_audio(self, _content: bytes, filename: str = "audio.webm") -> dict:
        """Placeholder for server-side STT. Frontend should send text for now."""
        return {
            "text": "",
            "filename": filename,
            "status": "not_implemented",
            "hint": "Use browser STT and POST /calls/{id}/turn with the transcript text.",
        }
