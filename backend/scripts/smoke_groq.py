#!/usr/bin/env python3
"""Smoke test: una vuelta de agente con Groq.

Uso (venv activo, desde backend/):

  PYTHONPATH=. python scripts/smoke_groq.py

Requiere GROQ_API_KEY en backend/.env
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.agent.factory import build_llm_client, describe_llm  # noqa: E402
from app.config import get_settings  # noqa: E402


async def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    info = describe_llm(settings)
    print("config:", info)

    if settings.llm_provider.strip().lower() != "groq":
        print("ERROR: pon LLM_PROVIDER=groq en backend/.env")
        return 1
    if not settings.groq_api_key.strip():
        print(
            "ERROR: falta GROQ_API_KEY.\n"
            "1) Entra a https://console.groq.com/keys\n"
            "2) Create API Key\n"
            "3) Pégala en backend/.env como GROQ_API_KEY=gsk_...\n"
            "4) Reinicia el backend y vuelve a correr este script"
        )
        return 1

    llm = build_llm_client(settings)
    result = await llm.complete(
        patient_name="María Demo",
        procedure="colecistectomía",
        dia_postop=3,
        message="Hola, me operaron hace tres días y me duele un poquito la herida, nada grave.",
        history=[],
        rag_context=[],
    )
    print("model:", llm.model_id)
    print("reply:", (result.get("reply") or "")[:300])
    print("escalate:", result.get("escalate"), result.get("escalate_reason"))
    print("OK — Groq respondió.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
