"""Shared TTS engine contract (DIP)."""

from __future__ import annotations

from typing import List, Optional, Protocol, Tuple


class TtsEnginePort(Protocol):
    """Server-side TTS adapter. Client (browser) TTS is outside this port."""

    def available(self) -> bool:
        """True when model/voice files are present and usable."""
        ...

    def list_voices(self) -> List[dict]:
        ...

    def status(self) -> dict:
        ...

    def warmup(self) -> None:
        ...

    def synthesize(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
    ) -> Tuple[bytes, str]:
        """Return (audio_bytes, content_type)."""
        ...
