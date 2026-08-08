from app.agent.factory import build_llm_client, describe_llm
from app.agent.llm_groq import GroqLLMClient
from app.agent.llm_mock import MockLLMClient
from app.config import Settings
import pytest


def test_mock_by_default():
    client = build_llm_client(Settings(llm_provider="mock", model_id="mock-x"))
    assert isinstance(client, MockLLMClient)


def test_groq_requires_key():
    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        build_llm_client(Settings(llm_provider="groq", groq_api_key="", model_id="llama"))


def test_groq_with_key():
    client = build_llm_client(
        Settings(llm_provider="groq", groq_api_key="gsk_test", model_id="llama-3.3-70b-versatile")
    )
    assert isinstance(client, GroqLLMClient)
    assert client.model_id == "llama-3.3-70b-versatile"


def test_describe_llm_ready():
    info = describe_llm(Settings(llm_provider="groq", groq_api_key="gsk_x", model_id="m"))
    assert info["llm_ready"] is True
    info2 = describe_llm(Settings(llm_provider="groq", groq_api_key="", model_id="m"))
    assert info2["llm_ready"] is False
