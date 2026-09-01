"""If the cloud LLM fails with a retryable error, keep the call on the fallback path."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agent.llm_delegate import delegate_complete
from app.agent.llm_errors import LLMError
from app.ports import LLMClient


class FallbackLLMClient:
    def __init__(self, primary: LLMClient, fallback: LLMClient) -> None:
        self._primary = primary
        self._fallback = fallback
        self.model_id = primary.model_id

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
        args = {
            "patient_name": patient_name,
            "procedure": procedure,
            "dia_postop": dia_postop,
            "message": message,
            "history": history,
            "rag_context": rag_context,
        }
        try:
            return await delegate_complete(self._primary, **args)
        except LLMError:
            parsed = await delegate_complete(self._fallback, **args)
            parsed["model_id"] = parsed.get("model_id") or self._fallback.model_id
            return parsed
