"""Factory for LLM clients (composition root helper)."""

from __future__ import annotations

from app.agent.llm_cascade import CascadeLLMClient, gemini_model_chain
from app.agent.llm_fallback import FallbackLLMClient
from app.agent.llm_fastpath import SafetyFastPathLLM
from app.agent.llm_gemini import GeminiLLMClient
from app.agent.llm_groq import GroqLLMClient
from app.agent.llm_mock import MockLLMClient
from app.config import Settings
from app.ports import LLMClient

# Challenge rule: only these LLM families (free cloud or local):
# Gemini Flash, Llama via Groq, local Llama 3.x, local Phi Mini.
# Anthropic / Claude is not allowed and fails the eliminatory model check.


def build_llm_client(settings: Settings) -> LLMClient:
    provider = (settings.llm_provider or "mock").strip().lower()

    if provider == "groq":
        if not settings.groq_api_key.strip():
            raise RuntimeError(
                "LLM_PROVIDER=groq pero GROQ_API_KEY está vacío. "
                "Crea una key en https://console.groq.com/keys y pégala en backend/.env"
            )
        return GroqLLMClient(
            model_id=settings.model_id,
            api_key=settings.groq_api_key.strip(),
        )

    if provider == "gemini":
        if not settings.gemini_api_key.strip():
            raise RuntimeError(
                "LLM_PROVIDER=gemini pero GEMINI_API_KEY está vacío. "
                "Crea una key en https://aistudio.google.com/ y pégala en backend/.env"
            )
        key = settings.gemini_api_key.strip()
        local = MockLLMClient(model_id="mock")
        flash_clients = [
            GeminiLLMClient(model_id=model_id, api_key=key)
            for model_id in gemini_model_chain(settings.model_id)
        ]
        cloud = FallbackLLMClient(CascadeLLMClient(flash_clients), local)
        return SafetyFastPathLLM(cloud, local)

    if provider in {"anthropic", "claude"}:
        raise RuntimeError(
            "LLM_PROVIDER=anthropic/claude is not allowed for this challenge. "
            "Use groq (Llama), gemini (Flash), or mock."
        )

    if provider != "mock":
        raise RuntimeError(
            f"LLM_PROVIDER={provider!r} no soportado. Usa: mock | groq | gemini"
        )

    return MockLLMClient(model_id=settings.model_id)


def describe_llm(settings: Settings) -> dict:
    """Safe status for /health (never exposes API keys)."""
    provider = (settings.llm_provider or "mock").strip().lower()
    ready = False
    detail = "mock (sin API)"
    if provider == "groq":
        ready = bool(settings.groq_api_key.strip())
        detail = "groq listo" if ready else "falta GROQ_API_KEY"
    elif provider == "gemini":
        ready = bool(settings.gemini_api_key.strip())
        detail = "gemini listo" if ready else "falta GEMINI_API_KEY"
    elif provider == "mock":
        ready = True
        detail = "mock"
    else:
        detail = f"provider desconocido: {provider}"
    return {
        "llm_provider": provider,
        "model_id": settings.model_id,
        "llm_ready": ready,
        "llm_detail": detail,
    }
