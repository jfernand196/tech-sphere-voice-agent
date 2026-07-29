"""Response parsing helpers for LLM output."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from app.schemas import KnowledgeChunk, SourceCitation


def parse_agent_json(raw: str) -> Dict[str, Any]:
    text = raw.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
    return {
        "reply": text or "No pude interpretar la respuesta del modelo.",
        "sources": [],
        "patient_state": {"symptoms": [], "severity": "none"},
        "escalate": False,
        "escalate_reason": None,
    }


def clean_excerpt(text: str, limit: int = 160) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def build_sources(
    parsed: Dict[str, Any],
    rag_hits: List[KnowledgeChunk],
) -> List[SourceCitation]:
    sources: List[SourceCitation] = []
    for item in parsed.get("sources") or []:
        try:
            sources.append(SourceCitation(**item))
        except Exception:
            continue
    if sources:
        return sources
    return [
        SourceCitation(
            doc_id=hit.doc_id,
            title=hit.title,
            chunk_id=hit.chunk_id,
            excerpt=clean_excerpt(hit.text),
        )
        for hit in rag_hits[:2]
    ]
