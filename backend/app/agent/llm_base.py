"""Shared LLM adapter flow (DRY): prompt → provider HTTP → parse JSON."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from app.agent.parsing import parse_agent_json
from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from app.metrics import Usage, attach_usage


class PromptedLLMClient(ABC):
    def __init__(self, *, model_id: str) -> None:
        self.model_id = model_id

    async def complete(
        self,
        *,
        patient_name: str,
        procedure: str,
        dia_postop: int,
        message: str,
        history: List[Dict[str, str]],
        rag_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        user_prompt = build_user_prompt(
            patient_name=patient_name,
            procedure=procedure,
            dia_postop=dia_postop,
            message=message,
            history=history,
            rag_context=rag_context,
        )
        raw, usage = await self._generate(system=SYSTEM_PROMPT, user=user_prompt)
        return attach_usage(parse_agent_json(raw), usage)

    @abstractmethod
    async def _generate(self, *, system: str, user: str) -> Tuple[str, Usage]:
        """Provider-specific HTTP call; return raw model text + optional usage."""
