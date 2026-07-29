"""Factory for LLM clients (composition root helper)."""

from __future__ import annotations

from app.agent.llm_anthropic import AnthropicLLMClient
from app.agent.llm_mock import MockLLMClient
from app.config import Settings
from app.ports import LLMClient


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return AnthropicLLMClient(
            model_id=settings.model_id,
            api_key=settings.anthropic_api_key,
        )
    return MockLLMClient(model_id=settings.model_id)
