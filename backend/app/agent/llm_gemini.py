"""Google Gemini Flash adapter — free AI Studio tier (allowed family for Tech Sphere G3)."""

from __future__ import annotations

import httpx

from app.agent.llm_base import PromptedLLMClient


class GeminiLLMClient(PromptedLLMClient):
    def __init__(self, *, model_id: str, api_key: str) -> None:
        super().__init__(model_id=model_id)
        self._api_key = api_key

    async def _generate(self, *, system: str, user: str) -> str:
        # Gemini generateContent: fold system into the user turn for broad API compatibility.
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"{system}\n\n---\n\n{user}"}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            },
        }
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model_id}:generateContent"
        )
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                params={"key": self._api_key},
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        parts = (
            ((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or []
        )
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))
