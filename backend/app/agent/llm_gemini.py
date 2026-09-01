"""Google Gemini Flash adapter — free AI Studio tier (challenge-allowed family)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import httpx

from app.agent.llm_base import PromptedLLMClient
from app.agent.llm_errors import LLMQuotaError, LLMTimeoutError, LLMUnavailableError
from app.metrics import Usage, usage_gemini

_CAPACITY_MARKERS = ("high demand", "try again later", "unavailable")

_INTERACTION_URLS = (
    "https://generativelanguage.googleapis.com/v1beta2/interactions",
    "https://generativelanguage.googleapis.com/v1beta/interactions",
)
# Voice cannot wait for Gemini 3 default thinking; fail fast and let the cascade try Lite.
_TIMEOUT = httpx.Timeout(connect=5.0, read=6.0, write=8.0, pool=5.0)


def _gemini_error_message(resp: httpx.Response) -> str:
    try:
        err = resp.json().get("error") or {}
        return str(err.get("message") or "")[:280]
    except Exception:
        return resp.reason_phrase


def _interaction_text(data: Dict[str, Any]) -> str:
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct
    chunks: List[str] = []
    for step in data.get("steps") or []:
        if not isinstance(step, dict):
            continue
        if step.get("type") not in {"model_output", "text", "output"}:
            continue
        for part in step.get("content") or []:
            if isinstance(part, dict) and part.get("text"):
                chunks.append(str(part["text"]))
    return "".join(chunks)


def _wants_minimal_thinking(model_id: str) -> bool:
    mid = model_id.lower()
    if "lite" in mid:
        return False
    return "gemini-3." in mid


def _generation_config(model_id: str) -> Dict[str, Any]:
    config: Dict[str, Any] = {
        "temperature": 0.2,
        "max_output_tokens": 1024,
    }
    if _wants_minimal_thinking(model_id):
        config["thinking_level"] = "minimal"
        config["thinking_summaries"] = "none"
    return config


def skip_to_next_flash(status_code: int, message: str) -> bool:
    """429 quota and retired model ids should walk the Flash cascade."""
    if status_code == 429:
        return True
    lowered = message.lower()
    if "quota exceeded" in lowered or "exceeded your current quota" in lowered:
        return True
    if "no longer available" in lowered:
        return True
    return False


def _interaction_payload(*, model_id: str, system: str, user: str) -> Dict[str, Any]:
    return {
        "model": model_id,
        "input": f"{system}\n\n---\n\n{user}",
        "store": False,
        "generation_config": _generation_config(model_id),
    }


class GeminiLLMClient(PromptedLLMClient):
    def __init__(self, *, model_id: str, api_key: str) -> None:
        super().__init__(model_id=model_id)
        self._api_key = api_key

    async def _generate(self, *, system: str, user: str) -> Tuple[str, Usage]:
        payload = _interaction_payload(model_id=self.model_id, system=system, user=user)
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self._api_key,
        }
        last_error = "Gemini no respondió."
        last_status = 0
        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                for url in _INTERACTION_URLS:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.is_success:
                        data = resp.json()
                        text = _interaction_text(data)
                        if not text.strip():
                            raise LLMUnavailableError(
                                "Gemini devolvió una respuesta vacía. Reintenta el turno."
                            )
                        return text, usage_gemini(data)
                    last_status = resp.status_code
                    last_error = _gemini_error_message(resp)
                    if resp.status_code not in {404, 405}:
                        break
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                "Gemini tardó demasiado. Reintenta el turno."
            ) from exc
        if skip_to_next_flash(last_status, last_error):
            raise LLMQuotaError(
                f"Gemini sin cupo o modelo retirado ({self.model_id})."
            )
        lowered = last_error.lower()
        if any(marker in lowered for marker in _CAPACITY_MARKERS):
            raise LLMUnavailableError(
                "Gemini está saturado o tardó demasiado. Reintenta el turno."
            )
        raise RuntimeError(
            f"Gemini HTTP error model={self.model_id}. {last_error} "
            "Las keys nuevas (AQ.) van por la API Interactions. "
            "Crea una key en https://aistudio.google.com/apikey y MODEL_ID=gemini-3.6-flash"
        )
