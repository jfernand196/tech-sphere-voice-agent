"""Shared LLM adapter flow (DRY): prompt → provider HTTP → parse JSON."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.agent.parsing import parse_agent_json
from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt


class PromptedLLMClient(ABC):
    def __init__(self, *, model_id: str) -> None:
        self.model_id = model_id

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
        raw = await self._generate(system=SYSTEM_PROMPT, user=user_prompt)
        return parse_agent_json(raw)

    @abstractmethod
    async def _generate(self, *, system: str, user: str) -> str:
        """Provider-specific HTTP call; return raw model text."""
