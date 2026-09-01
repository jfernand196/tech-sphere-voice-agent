"""Skip the cloud LLM when safety already decided to escalate."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agent.llm_delegate import delegate_complete
from app.agent.safety import assess_message
from app.ports import LLMClient


class SafetyFastPathLLM:
    def __init__(self, primary: LLMClient, fast_path: LLMClient) -> None:
        self._primary = primary
        self._fast_path = fast_path
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
        client = self._fast_path if assess_message(message).escalate else self._primary
        parsed = await delegate_complete(
            client,
            patient_name=patient_name,
            procedure=procedure,
            dia_postop=dia_postop,
            message=message,
            history=history,
            rag_context=rag_context,
        )
        parsed["model_id"] = parsed.get("model_id") or client.model_id
        return parsed
