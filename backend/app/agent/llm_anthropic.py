"""Anthropic LLM adapter (OCP: swap without changing AgentService)."""

from __future__ import annotations

from typing import Any, Dict, List

import httpx

from app.agent.parsing import parse_agent_json
from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt


class AnthropicLLMClient:
    def __init__(self, *, model_id: str, api_key: str) -> None:
        self.model_id = model_id
        self._api_key = api_key

    async def complete(
        self,
        *,
        patient_name: str,
        procedure: str,
        message: str,
        history: List[Dict[str, str]],
        rag_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        user_prompt = build_user_prompt(
            patient_name=patient_name,
            procedure=procedure,
            message=message,
            history=history,
            rag_context=rag_context,
        )
        payload = {
            "model": self.model_id,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        parts = data.get("content") or []
        raw = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        return parse_agent_json(raw)
