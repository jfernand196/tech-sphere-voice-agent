"""Shared LLMClient.complete call (avoids repeating the port kwargs)."""

from __future__ import annotations

from typing import Any, Dict, List

from app.ports import LLMClient


async def delegate_complete(
    client: LLMClient,
    *,
    patient_name: str,
    procedure: str,
    dia_postop: int,
    message: str,
    history: List[Dict[str, str]],
    rag_context: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return await client.complete(
        patient_name=patient_name,
        procedure=procedure,
        dia_postop=dia_postop,
        message=message,
        history=history,
        rag_context=rag_context,
    )
