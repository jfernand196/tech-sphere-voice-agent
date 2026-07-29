"""Voice adapters.

Scaffold strategy:
- Browser handles STT/TTS for the MVP (Web Speech API).
- This module is the server-side seam to plug Deepgram/Whisper/ElevenLabs later
  without changing the agent/RAG core.
"""

from __future__ import annotations


class VoiceService:
    def __init__(self) -> None:
        self.mode = "browser"

    def capabilities(self) -> dict:
        return {
            "mode": self.mode,
            "stt": "browser-web-speech-api (client) | server stub ready",
            "tts": "browser-speechSynthesis (client) | server stub ready",
            "telephony": False,
            "note": "No real telephony required for the challenge.",
        }

    async def transcribe_audio(self, _content: bytes, filename: str = "audio.webm") -> dict:
        """Placeholder for server-side STT. Frontend should send text for now."""
        return {
            "text": "",
            "filename": filename,
            "status": "not_implemented",
            "hint": "Use browser STT and POST /calls/{id}/turn with the transcript text.",
        }
