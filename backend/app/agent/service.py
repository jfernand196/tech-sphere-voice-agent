"""Agent orchestration use-case (DIP: depends on KnowledgePort + LLMClient)."""

from __future__ import annotations

import time
from typing import Dict, List

from app.agent.parsing import build_sources
from app.agent.safety import apply_safety_overrides
from app.ports import KnowledgePort, LLMClient
from app.schemas import AgentTurnResponse, PatientState, Severity


class AgentService:
    def __init__(self, knowledge: KnowledgePort, llm: LLMClient) -> None:
        self._knowledge = knowledge
        self._llm = llm

    async def respond(
        self,
        *,
        patient_name: str,
        procedure: str,
        dia_postop: int,
        message: str,
        history: List[Dict[str, str]],
    ) -> AgentTurnResponse:
        started = time.perf_counter()
        rag_hits = self._knowledge.retrieve(message, top_k=4)
        rag_context = [hit.model_dump() for hit in rag_hits]

        parsed = await self._llm.complete(
            patient_name=patient_name,
            procedure=procedure,
            dia_postop=dia_postop,
            message=message,
            history=history,
            rag_context=rag_context,
        )

        try:
            state = PatientState(**(parsed.get("patient_state") or {}))
        except Exception:
            state = PatientState(
                symptoms=[],
                severity=Severity.none,
                notes=message[:200],
            )

        escalate, reason, state = apply_safety_overrides(
            message,
            escalate=bool(parsed.get("escalate")),
            escalate_reason=parsed.get("escalate_reason"),
            patient_state=state,
        )

        return AgentTurnResponse(
            reply=str(parsed.get("reply") or "¿Me puedes contar un poco más cómo te sientes?"),
            sources=build_sources(parsed, rag_hits),
            patient_state=state,
            escalate=escalate,
            escalate_reason=reason,
            model_id=self._llm.model_id,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
