"""Voice adapters: browser STT (client) + Kokoro/Piper server TTS."""

from __future__ import annotations

from typing import Dict, Literal, Optional

from app.config import Settings, get_settings
from app.voice.base import TtsEnginePort
from app.voice.kokoro_engine import KokoroEngine
from app.voice.piper_engine import PiperEngine

ServerTtsEngine = Literal["kokoro", "piper"]
ENGINE_LABELS: Dict[ServerTtsEngine, str] = {
    "kokoro": "kokoro-onnx (server WAV)",
    "piper": "piper-tts (server WAV)",
}


class VoiceService:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        kokoro: Optional[TtsEnginePort] = None,
        piper: Optional[TtsEnginePort] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.engines: Dict[ServerTtsEngine, TtsEnginePort] = {
            "kokoro": kokoro or KokoroEngine(self.settings),
            "piper": piper or PiperEngine(self.settings),
        }

    @property
    def kokoro(self) -> TtsEnginePort:
        return self.engines["kokoro"]

    @property
    def piper(self) -> TtsEnginePort:
        return self.engines["piper"]

    def _provider_allows(self, engine: ServerTtsEngine) -> bool:
        provider = self.settings.tts_provider.strip().lower()
        if provider == "browser":
            return False
        if provider == "auto":
            return True
        return provider == engine

    def engine_available(self, engine: ServerTtsEngine) -> bool:
        return self._provider_allows(engine) and self.engines[engine].available()

    def kokoro_available(self) -> bool:
        return self.engine_available("kokoro")

    def piper_available(self) -> bool:
        return self.engine_available("piper")

    def capabilities(self) -> dict:
        engines_out: dict = {
            "browser": {
                "available": True,
                "kind": "client-speechSynthesis",
            },
        }
        for name, eng in self.engines.items():
            ok = self.engine_available(name)
            engines_out[name] = {
                "available": ok,
                "kind": ENGINE_LABELS[name],
                **eng.status(),
            }
        return {
            "stt": "browser-web-speech-api (client)",
            "tts_provider_setting": self.settings.tts_provider.strip().lower(),
            "engines": engines_out,
            "telephony": False,
            "note": "STT is browser-only; server exposes TTS when Kokoro/Piper are warmed.",
        }

    def _resolve_engine(self, engine: Optional[str]) -> ServerTtsEngine:
        requested = (engine or "").strip().lower()
        if requested not in {"", "auto", "kokoro", "piper"}:
            raise RuntimeError(f"Unsupported TTS engine: {requested!r}")

        if requested == "piper":
            if not self.engine_available("piper"):
                raise RuntimeError(
                    "Piper TTS is not active. Set TTS_PROVIDER=piper|auto and run make warm-piper."
                )
            return "piper"

        # kokoro | auto | empty — prefer Kokoro, then Piper.
        if self.engine_available("kokoro"):
            return "kokoro"
        if self.engine_available("piper"):
            return "piper"
        raise RuntimeError(
            "Server TTS is not active. Run make warm-kokoro and/or make warm-piper "
            "(TTS_PROVIDER=auto|kokoro|piper)."
        )

    def synthesize_tts(
        self,
        text: str,
        *,
        engine: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> tuple[bytes, str]:
        chosen = self._resolve_engine(engine)
        resolved_speed = speed
        if resolved_speed is None and chosen == "piper":
            resolved_speed = self.settings.piper_speed
        return self.engines[chosen].synthesize(
            text,
            voice=voice,
            speed=resolved_speed,
        )
