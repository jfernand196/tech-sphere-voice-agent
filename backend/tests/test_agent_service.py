from typing import Any, Dict, List

import asyncio

from app.agent.reply_guard import SPOKEN_ALERT_SENTENCE, SPOKEN_WATCH_PLAN
from app.agent.service import AgentService
from app.schemas import KnowledgeChunk


class _EmptyKnowledge:
    def retrieve(self, query: str, top_k: int = 4) -> List[KnowledgeChunk]:
        _ = (query, top_k)
        return []


class _SilentEscalateLlm:
    """Simulates Groq: no spoken alert and escalate=false; safety must still speak."""

    model_id = "test-silent"

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
        _ = (patient_name, procedure, dia_postop, message, history, rag_context)
        return {
            "reply": "Es importante que te cuides. ¿Has notado náuseas?",
            "sources": [],
            "patient_state": {
                "symptoms": ["fiebre"],
                "severity": "moderate",
                "notes": "",
            },
            "escalate": False,
            "escalate_reason": None,
        }


def test_agent_cancels_false_escalate_on_denial_followup() -> None:
    class _CaptureKnowledge:
        def __init__(self) -> None:
            self.queries: List[str] = []

        def retrieve(self, query: str, top_k: int = 4) -> List[KnowledgeChunk]:
            self.queries.append(query)
            _ = top_k
            return [
                KnowledgeChunk(
                    chunk_id="c1",
                    doc_id="d1",
                    title="Protocolo post-operatorio genérico",
                    text="Mantener la herida limpia y seca.",
                    score=1.0,
                )
            ]

    class _FalseAlarmLlm:
        model_id = "gemini-3.5-flash"

        async def complete(self, **kwargs: Any) -> Dict[str, Any]:
            _ = kwargs
            return {
                "reply": (
                    "Me alegra saber que no tiene esos síntomas, Manuel. "
                    "Voy a comunicar su situación con un profesional de salud. "
                    "Si se siente peor, acuda a urgencias."
                ),
                "sources": [],
                "patient_state": {
                    "symptoms": ["fiebre", "dolor"],
                    "severity": "moderate",
                    "notes": "",
                },
                "escalate": True,
                "escalate_reason": "Febrícula y dolor moderado",
                "model_id": "gemini-3.5-flash",
            }

    knowledge = _CaptureKnowledge()
    agent = AgentService(knowledge, _FalseAlarmLlm())
    turn = asyncio.run(
        agent.respond(
            patient_name="Manuel Castillo",
            procedure="colecistectomía",
            dia_postop=3,
            message="Por el momento no he notado eso",
            history=[
                {
                    "role": "patient",
                    "content": "Hola tengo fiebre 37,4 y tengo un dolor 5 de 10 qué hago",
                }
            ],
        )
    )
    assert turn.escalate is False
    assert SPOKEN_ALERT_SENTENCE not in turn.reply
    assert "profesional de salud" not in turn.reply.lower()
    assert "Me alegra saber" in turn.reply
    assert knowledge.queries
    assert "fiebre" in knowledge.queries[0].lower()


def test_agent_speaks_alert_when_safety_overrides_silent_model() -> None:
    agent = AgentService(_EmptyKnowledge(), _SilentEscalateLlm())
    turn = asyncio.run(
        agent.respond(
            patient_name="Ana Ángela Sánchez",
            procedure="colecistectomía",
            dia_postop=7,
            message="Hola tengo secreción purulenta y tengo fiebre de 38",
            history=[],
        )
    )
    assert turn.escalate is True
    assert SPOKEN_ALERT_SENTENCE in turn.reply
    assert SPOKEN_WATCH_PLAN in turn.reply
    assert "náuseas" in turn.reply
