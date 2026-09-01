import asyncio
from typing import Any, Dict

from app.agent.llm_errors import LLMTimeoutError
from app.agent.llm_fallback import FallbackLLMClient
from app.agent.llm_fastpath import SafetyFastPathLLM
from app.agent.llm_mock import MockLLMClient


class _BoomLlm:
    model_id = "gemini-3.6-flash"

    async def complete(self, **kwargs: Any) -> Dict[str, Any]:
        raise LLMTimeoutError("Gemini tardó demasiado. Reintenta el turno.")


def test_fallback_uses_mock_when_primary_times_out() -> None:
    client = FallbackLLMClient(_BoomLlm(), MockLLMClient(model_id="gemini-3.6-flash"))
    parsed = asyncio.run(
        client.complete(
            patient_name="Ana",
            procedure="colecistectomía",
            dia_postop=7,
            message="me duele un poco la herida",
            history=[],
            rag_context=[
                {
                    "doc_id": "d1",
                    "title": "Protocolo de herida",
                    "chunk_id": "c1",
                    "text": "Mantener la herida limpia y seca.",
                }
            ],
        )
    )
    assert parsed["reply"]
    assert client.model_id == "gemini-3.6-flash"
    assert parsed["model_id"] == "gemini-3.6-flash"


class _MustNotRun:
    model_id = "gemini-3.6-flash"

    async def complete(self, **kwargs: Any) -> Dict[str, Any]:
        raise AssertionError("cloud LLM must be skipped when safety already escalates")


def test_fast_path_skips_cloud_llm_on_safety_escalate() -> None:
    client = SafetyFastPathLLM(_MustNotRun(), MockLLMClient(model_id="gemini-3.6-flash"))
    parsed = asyncio.run(
        client.complete(
            patient_name="Ana",
            procedure="colecistectomía",
            dia_postop=7,
            message="secreción purulenta y fiebre de 38 grados",
            history=[],
            rag_context=[],
        )
    )
    assert parsed["escalate"] is True
    assert parsed["model_id"] == "gemini-3.6-flash"
