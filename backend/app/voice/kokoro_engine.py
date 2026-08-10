"""Lazy Kokoro ONNX TTS (Spanish-ready). Optional — falls back to browser TTS."""

from __future__ import annotations

import io
import threading
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import Settings

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
        self.last_error: Optional[str] = None

    @property
    def model_path(self) -> Path:
        return self.settings.kokoro_model_path

    @property
    def voices_path(self) -> Path:
        return self.settings.kokoro_voices_path

    def files_present(self) -> bool:
        return self.model_path.is_file() and self.voices_path.is_file()

    def available(self) -> bool:
        return self.files_present()

    def list_voices(self) -> List[dict]:
        return [{"id": vid, "label": label} for vid, label in SUPPORTED_VOICES]

    def status(self) -> dict:
        return {
            "files_present": self.files_present(),
            "loaded": self._kokoro is not None,
            "model_path": str(self.model_path),
            "voices_path": str(self.voices_path),
            "default_voice": self.settings.kokoro_voice or DEFAULT_KOKORO_VOICE,
            "error": self.last_error,
            "voices": self.list_voices(),
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
            try:
                from kokoro_onnx import Kokoro

                self._kokoro = Kokoro(str(self.model_path), str(self.voices_path))
                self.last_error = None
            except Exception as exc:  # noqa: BLE001 — surfaced via status / HTTP
                self.last_error = str(exc)
                raise

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
