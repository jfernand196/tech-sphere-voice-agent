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

    llm_provider: str = "mock"
    model_id: str = "claude-haiku-placeholder"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
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
