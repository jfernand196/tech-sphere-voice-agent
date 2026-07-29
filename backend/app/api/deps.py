"""Composition root: wires adapters into use-cases (DIP)."""

from functools import lru_cache

from app.agent.factory import build_llm_client
from app.agent.service import AgentService
from app.calls.service import CallService
from app.config import Settings, get_settings
from app.rag.service import KnowledgeService
from app.voice.service import VoiceService


@lru_cache
def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService(get_settings())


@lru_cache
def get_call_service() -> CallService:
    return CallService(get_settings().calls_path)


@lru_cache
def get_agent_service() -> AgentService:
    settings = get_settings()
    return AgentService(
        knowledge=get_knowledge_service(),
        llm=build_llm_client(settings),
    )


@lru_cache
def get_voice_service() -> VoiceService:
    return VoiceService()


def settings() -> Settings:
    return get_settings()
