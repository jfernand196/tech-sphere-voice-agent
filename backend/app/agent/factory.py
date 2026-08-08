"""Factory for LLM clients (composition root helper)."""

from __future__ import annotations

from app.agent.llm_gemini import GeminiLLMClient
from app.agent.llm_groq import GroqLLMClient
from app.agent.llm_mock import MockLLMClient
from app.config import Settings
from app.ports import LLMClient

# Allowed families (Tech Sphere G3): Gemini Flash, Llama via Groq, local Llama/Phi.
# Anthropic / Claude is NOT allowed — using it disqualifies the submission.


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
        return GeminiLLMClient(
            model_id=settings.model_id,
            api_key=settings.gemini_api_key.strip(),
        )

    if provider in {"anthropic", "claude"}:
        raise RuntimeError(
            "LLM_PROVIDER=anthropic/claude no está permitido en Tech Sphere 2026 "
            "(compuerta G3). Usa groq (Llama), gemini (Flash), o mock."
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
