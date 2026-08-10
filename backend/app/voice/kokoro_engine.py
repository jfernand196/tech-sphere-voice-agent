"""Lazy Kokoro ONNX TTS (Spanish-ready). Optional — falls back to browser TTS."""

from __future__ import annotations

import io
import threading
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import Settings, get_settings

# Spanish clinical demo voice (Kokoro multilingual).
DEFAULT_KOKORO_VOICE = "ef_dora"
DEFAULT_KOKORO_LANG = "es"
SUPPORTED_VOICES = (
    ("ef_dora", "Kokoro Dora (ES · mujer)"),
    ("em_alex", "Kokoro Alex (ES · hombre)"),
    ("em_santa", "Kokoro Santa (ES · hombre)"),
)


class KokoroEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._kokoro = None
        self._error: Optional[str] = None

    @property
    def model_path(self) -> Path:
        return self.settings.kokoro_model_path

    @property
    def voices_path(self) -> Path:
        return self.settings.kokoro_voices_path

    def files_present(self) -> bool:
        return self.model_path.is_file() and self.voices_path.is_file()

    def available(self) -> bool:
        """True when provider wants Kokoro and model files are on disk (lazy-load later)."""
        if self.settings.tts_provider.strip().lower() not in {"kokoro", "auto"}:
            return False
        return self.files_present()

    def status(self) -> dict:
        provider = self.settings.tts_provider.strip().lower()
        return {
            "provider_setting": provider,
            "files_present": self.files_present(),
            "ready": self.available(),
            "loaded": self._kokoro is not None,
            "model_path": str(self.model_path),
            "voices_path": str(self.voices_path),
            "default_voice": self.settings.kokoro_voice,
            "error": self._error,
            "voices": [{"id": vid, "label": label} for vid, label in SUPPORTED_VOICES],
        }

    def _ensure_loaded(self) -> None:
        if self._kokoro is not None:
            return
        with self._lock:
            if self._kokoro is not None:
                return
            if not self.files_present():
                raise FileNotFoundError(
                    f"Kokoro model files missing. Run: make warm-kokoro "
                    f"(expected {self.model_path.name} + {self.voices_path.name})"
                )
            from kokoro_onnx import Kokoro

            self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))
            self._error = None

    def warmup(self) -> None:
        self._ensure_loaded()
        _ = self.synthesize("Hola.", voice=self.settings.kokoro_voice)

    def synthesize(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> Tuple[bytes, str]:
        """Return (wav_bytes, content_type)."""
        cleaned = (text or "").strip()
        if not cleaned:
            raise ValueError("text is empty")
        self._ensure_loaded()
        assert self._kokoro is not None
        import soundfile as sf

        voice_id = (voice or self.settings.kokoro_voice or DEFAULT_KOKORO_VOICE).strip()
        rate = float(speed if speed is not None else self.settings.kokoro_speed)
        rate = max(0.6, min(1.4, rate))
        samples, sample_rate = self._kokoro.create(
            cleaned,
            voice=voice_id,
            speed=rate,
            lang=DEFAULT_KOKORO_LANG,
        )
        buf = io.BytesIO()
        sf.write(buf, samples, sample_rate, format="WAV")
        return buf.getvalue(), "audio/wav"

    def list_voices(self) -> List[dict]:
        return [{"id": vid, "label": label} for vid, label in SUPPORTED_VOICES]


@lru_cache
def get_kokoro_engine() -> KokoroEngine:
    return KokoroEngine(get_settings())
