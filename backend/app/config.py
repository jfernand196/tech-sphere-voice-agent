from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Allowed: mock | groq | gemini  (see official-kit/docs/stack-tecnico.md)
    llm_provider: str = "mock"
    # Suggested defaults: llama-3.3-70b-versatile (Groq) or gemini-2.0-flash
    model_id: str = "llama-3.3-70b-versatile"
    groq_api_key: str = ""
    gemini_api_key: str = ""

    # RAG embeddings: fastembed (MiniLM multilingual, default) | hash (offline / rollback)
    embed_provider: str = "fastembed"

    cors_origins: str = "http://localhost:5173"

    data_dir: Path = _BACKEND_ROOT / "data"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def vector_store_dir(self) -> Path:
        return self.data_dir / "vector_store"

    @property
    def documents_path(self) -> Path:
        return self.data_dir / "documents.json"

    @property
    def calls_path(self) -> Path:
        return self.data_dir / "calls.json"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.vector_store_dir.mkdir(parents=True, exist_ok=True)
    return settings
