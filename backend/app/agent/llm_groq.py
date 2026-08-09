"""Groq LLM adapter — Meta Llama on the free tier (challenge-allowed family)."""

from __future__ import annotations

from typing import Tuple

import httpx

from app.agent.llm_base import PromptedLLMClient
from app.metrics import Usage, usage_openai_compat


class GroqLLMClient(PromptedLLMClient):
    """OpenAI-compatible Chat Completions against Groq Cloud."""

    def __init__(self, *, model_id: str, api_key: str) -> None:
        super().__init__(model_id=model_id)
        self._api_key = api_key

    async def _generate(self, *, system: str, user: str) -> Tuple[str, Usage]:
        payload = {
            "model": self.model_id,
            "temperature": 0.2,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        return text, usage_openai_compat(data)
