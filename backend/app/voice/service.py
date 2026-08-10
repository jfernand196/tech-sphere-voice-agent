"""Voice adapters: browser STT + Kokoro (or browser) TTS."""

from __future__ import annotations

from typing import Optional

from app.config import Settings, get_settings
from app.voice.kokoro_engine import KokoroEngine


class VoiceService:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        engine: Optional[KokoroEngine] = None,
    ) -> None:
        self.settings = settings or get_settings()
        # Inject engine in tests; production wires the same Settings instance (DIP).
        self.kokoro = engine or KokoroEngine(self.settings)

    def effective_tts_mode(self) -> str:
        provider = self.settings.tts_provider.strip().lower()
        if provider == "browser":
            return "browser"
        if provider in {"kokoro", "auto"} and self.kokoro.files_present():
            return "kokoro"
        return "browser"

    def capabilities(self) -> dict:
        mode = self.effective_tts_mode()
        return {
            "mode": mode,
            "stt": "browser-web-speech-api (client)",
            "tts": (
                "kokoro-onnx (server WAV)"
                if mode == "kokoro"
                else "browser-speechSynthesis (client)"
            ),
            "tts_provider_setting": self.settings.tts_provider.strip().lower(),
            "kokoro": self.kokoro.status(),
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
        if self.effective_tts_mode() != "kokoro":
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
