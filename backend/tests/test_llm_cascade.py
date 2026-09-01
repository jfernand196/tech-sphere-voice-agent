from typing import Any, Dict, List

import asyncio

from app.agent.llm_cascade import CascadeLLMClient, FLASH_LADDER, gemini_model_chain
from app.agent.llm_errors import LLMQuotaError, LLMTimeoutError
from app.agent.llm_fallback import FallbackLLMClient
from app.agent.llm_mock import MockLLMClient


def test_gemini_chain_starts_at_primary() -> None:
    assert gemini_model_chain("gemini-3.6-flash") == list(FLASH_LADDER)
    assert gemini_model_chain("gemini-3.5-flash") == [
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]
    assert gemini_model_chain("gemini-3.5-flash-lite") == [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]
    assert gemini_model_chain("gemini-3.1-flash-lite") == ["gemini-3.1-flash-lite"]


def test_gemini_chain_keeps_unknown_primary_first() -> None:
    assert gemini_model_chain("gemini-3.0-flash")[0] == "gemini-3.0-flash"
    assert "gemini-3.5-flash-lite" in gemini_model_chain("gemini-3.0-flash")


class _QuotaLlm:
    def __init__(self, model_id: str, hits: List[str]) -> None:
        self.model_id = model_id
        self._hits = hits

    async def complete(self, **kwargs: Any) -> Dict[str, Any]:
        self._hits.append(self.model_id)
        raise LLMQuotaError(f"quota {self.model_id}")


class _OkLlm:
    def __init__(self, model_id: str, hits: List[str]) -> None:
        self.model_id = model_id
        self._hits = hits

    async def complete(self, **kwargs: Any) -> Dict[str, Any]:
        self._hits.append(self.model_id)
        return {
            "reply": f"ok-{self.model_id}",
            "sources": [],
            "patient_state": {"symptoms": [], "severity": "none"},
            "escalate": False,
            "escalate_reason": None,
        }


class _TimeoutLlm:
    model_id = "gemini-3.6-flash"

    async def complete(self, **kwargs: Any) -> Dict[str, Any]:
        raise LLMTimeoutError("timeout")


_TURN = {
    "patient_name": "Ana",
    "procedure": "colecistectomía",
    "dia_postop": 7,
    "message": "me duele un poco la herida",
    "history": [],
    "rag_context": [],
}


def test_cascade_skips_quota_to_next_flash() -> None:
    hits: List[str] = []
    client = CascadeLLMClient(
        [
            _QuotaLlm("gemini-3.6-flash", hits),
            _OkLlm("gemini-3.5-flash", hits),
            _OkLlm("gemini-3.5-flash-lite", hits),
        ]
    )
    parsed = asyncio.run(client.complete(**_TURN))
    assert hits == ["gemini-3.6-flash", "gemini-3.5-flash"]
    assert parsed["reply"] == "ok-gemini-3.5-flash"
    assert parsed["model_id"] == "gemini-3.5-flash"


def test_cascade_walks_to_lite_then_mock() -> None:
    hits: List[str] = []
    cascade = CascadeLLMClient(
        [
            _QuotaLlm("gemini-3.6-flash", hits),
            _QuotaLlm("gemini-3.5-flash", hits),
            _QuotaLlm("gemini-3.5-flash-lite", hits),
            _QuotaLlm("gemini-3.1-flash-lite", hits),
        ]
    )
    client = FallbackLLMClient(cascade, MockLLMClient(model_id="mock"))
    parsed = asyncio.run(client.complete(**_TURN))
    assert hits == [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ]
    assert parsed["reply"]


def test_cascade_walks_on_timeout_to_next_flash() -> None:
    hits: List[str] = []
    client = CascadeLLMClient(
        [_TimeoutLlm(), _OkLlm("gemini-3.5-flash", hits)]
    )
    parsed = asyncio.run(client.complete(**_TURN))
    assert hits == ["gemini-3.5-flash"]
    assert parsed["model_id"] == "gemini-3.5-flash"


def test_cascade_skips_exhausted_model_on_next_turn() -> None:
    hits: List[str] = []
    client = CascadeLLMClient(
        [
            _QuotaLlm("gemini-3.6-flash", hits),
            _OkLlm("gemini-3.5-flash", hits),
        ]
    )
    asyncio.run(client.complete(**_TURN))
    hits.clear()
    parsed = asyncio.run(client.complete(**_TURN))
    assert hits == ["gemini-3.5-flash"]
    assert parsed["model_id"] == "gemini-3.5-flash"


def test_cascade_skips_timed_out_model_on_next_turn() -> None:
    hits: List[str] = []

    class _CountingTimeout:
        model_id = "gemini-3.6-flash"

        async def complete(self, **kwargs: Any) -> Dict[str, Any]:
            hits.append(self.model_id)
            raise LLMTimeoutError("timeout")

    client = CascadeLLMClient(
        [_CountingTimeout(), _OkLlm("gemini-3.5-flash", hits)]
    )
    asyncio.run(client.complete(**_TURN))
    hits.clear()
    parsed = asyncio.run(client.complete(**_TURN))
    assert hits == ["gemini-3.5-flash"]
    assert parsed["model_id"] == "gemini-3.5-flash"
