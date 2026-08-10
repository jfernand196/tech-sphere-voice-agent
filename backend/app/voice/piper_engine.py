"""Lazy Piper TTS (Spanish MX voices). Optional — UI falls back to browser TTS."""

from __future__ import annotations

import io
import threading
import wave
from pathlib import Path
from typing import List, Optional, Tuple

from app.config import Settings

# LatAm Spanish voices (Mexico models — closest free Piper pack for CO demo).
DEFAULT_PIPER_VOICE = "es_MX-ald-medium"
SUPPORTED_VOICES = (
    ("es_MX-ald-medium", "Piper Ald (ES-MX · media · rápida)"),
    ("es_MX-claude-high", "Piper Claude (ES-MX · alta)"),
)
_SUPPORTED_IDS = {vid for vid, _ in SUPPORTED_VOICES}


class PiperEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._lock = threading.Lock()
        self._voices: dict[str, object] = {}
        self.last_error: Optional[str] = None

    @property
    def voices_dir(self) -> Path:
        return self.settings.piper_dir

    def configured_voice(self) -> str:
        return (self.settings.piper_voice or DEFAULT_PIPER_VOICE).strip()

    def voice_model_path(self, voice_id: str) -> Path:
        return self.voices_dir / f"{voice_id}.onnx"

    def files_present(self, voice_id: Optional[str] = None) -> bool:
        vid = (voice_id or self.configured_voice()).strip()
        model = self.voice_model_path(vid)
        config = Path(str(model) + ".json")
        return model.is_file() and config.is_file()

    def available_voice_ids(self) -> List[str]:
        return [vid for vid, _ in SUPPORTED_VOICES if self.files_present(vid)]

    def available(self) -> bool:
        return bool(self.available_voice_ids())

    def list_voices(self) -> List[dict]:
        return [
            {"id": vid, "label": label}
            for vid, label in SUPPORTED_VOICES
            if self.files_present(vid)
        ]

    def status(self) -> dict:
        return {
            "files_present": self.available(),
            "loaded": bool(self._voices),
            "voices_dir": str(self.voices_dir),
            "default_voice": self.configured_voice(),
            "error": self.last_error,
            "voices": self.list_voices(),
        }

    def _ensure_loaded(self, voice_id: str):
        if voice_id in self._voices:
            return self._voices[voice_id]
        with self._lock:
            cached = self._voices.get(voice_id)
            if cached is not None:
                return cached
            model = self.voice_model_path(voice_id)
            if not model.is_file():
                raise FileNotFoundError(
                    f"Piper voice missing. Run: make warm-piper "
                    f"(expected {model.name} under {self.voices_dir})"
                )
            try:
                from piper import PiperVoice

                voice = PiperVoice.load(model)
                self._voices[voice_id] = voice
                self.last_error = None
                return voice
            except Exception as exc:  # noqa: BLE001
                self.last_error = str(exc)
                raise

    def warmup(self) -> None:
        _ = self.synthesize("Hola.", voice=self.configured_voice())

    def _pick_voice_id(self, voice: Optional[str]) -> str:
        voice_id = (voice or self.configured_voice()).strip()
        if voice_id not in _SUPPORTED_IDS:
            voice_id = DEFAULT_PIPER_VOICE
        if self.files_present(voice_id):
            return voice_id
        available = self.available_voice_ids()
        if not available:
            raise FileNotFoundError("Piper voices missing. Run: make warm-piper")
        return available[0]

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

        voice_id = self._pick_voice_id(voice)

        piper_voice = self._ensure_loaded(voice_id)
        from piper import SynthesisConfig

        length_scale = None
        if speed is not None:
            # Piper length_scale: lower = faster. Map UI speed 0.6–1.4 → ~1.4–0.7.
            rate = max(0.6, min(1.4, float(speed)))
            length_scale = max(0.7, min(1.4, 2.0 - rate))

        syn_config = SynthesisConfig(length_scale=length_scale) if length_scale else None
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            piper_voice.synthesize_wav(cleaned, wav_file, syn_config=syn_config)
        return buf.getvalue(), "audio/wav"
