"""Try the next Gemini Flash when the current one is quota-exhausted or retired."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from app.agent.llm_delegate import delegate_complete
from app.agent.llm_errors import LLMQuotaError, LLMTimeoutError, LLMUnavailableError
from app.ports import LLMClient

_SKIP_TO_NEXT = (LLMQuotaError, LLMTimeoutError, LLMUnavailableError)
FLASH_LADDER = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
)


class ExhaustedFlashCache:
    """Process-memory skip list: a 429/timeout on 3.6 must not be retried next turn."""

    def __init__(self) -> None:
        self._model_ids: set[str] = set()

    def mark(self, model_id: str) -> None:
        key = (model_id or "").strip()
        if key:
            self._model_ids.add(key)

    def is_marked(self, model_id: str) -> bool:
        return (model_id or "").strip() in self._model_ids


def gemini_model_chain(primary: str) -> List[str]:
    """Primary first, then cheaper Flash models still on this account's free tier."""
    key = (primary or "").strip()
    if key in FLASH_LADDER:
        return list(FLASH_LADDER[FLASH_LADDER.index(key) :])
    rest = [model for model in FLASH_LADDER if model != key]
    return [key] + rest if key else list(FLASH_LADDER)


class CascadeLLMClient:
    """Walk clients until one succeeds; quota, timeout, or saturation advance the chain."""

    def __init__(
        self,
        clients: Sequence[LLMClient],
        exhausted: ExhaustedFlashCache | None = None,
    ) -> None:
        if not clients:
            raise ValueError("CascadeLLMClient needs at least one client")
        self._clients = list(clients)
        self._exhausted = exhausted or ExhaustedFlashCache()
        self.model_id = self._clients[0].model_id

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
        last_skip: LLMQuotaError | LLMTimeoutError | LLMUnavailableError | None = None
        attempted = False
        for client in self._clients:
            if self._exhausted.is_marked(client.model_id):
                continue
            attempted = True
            try:
                parsed = await delegate_complete(client, **args)
                parsed["model_id"] = client.model_id
                return parsed
            except _SKIP_TO_NEXT as exc:
                self._exhausted.mark(client.model_id)
                last_skip = exc
        if last_skip is None and not attempted:
            raise LLMQuotaError("Gemini sin cupo en todos los Flash de la cadena.")
        if last_skip is None:
            raise RuntimeError("Gemini cascade had no client to call.")
        raise last_skip
