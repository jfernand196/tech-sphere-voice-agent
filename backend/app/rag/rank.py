"""Clinical citation ranking (SRP: not indexing, not HTTP)."""

from __future__ import annotations

from typing import Dict, Sequence

from app.agent.safety import wants_wound_followup
from app.schemas import KnowledgeChunk

FOLLOWUP_QUERY_EXPANSION = (
    "herida quirúrgica secreción purulenta signos de alarma postoperatorio"
)
FOLLOWUP_DOC_HINTS = (
    "secreción purulenta",
    "secrecion purulenta",
    "herida",
    "post-operatorio",
    "postoperatorio",
    "signos de alarma",
    "seguimiento",
    "infección",
    "infeccion",
)
DIAGNOSIS_TITLE_HINTS = (
    "diagnóstico",
    "diagnostico",
    "colelitiasis",
    "colecistitis aguda",
)
HINT_MATCH_WEIGHT = 2
DIAGNOSIS_TITLE_PENALTY = 4
CANDIDATE_POOL_FACTOR = 3


def rewrite_followup_query(query: str) -> str:
    if not wants_wound_followup(query):
        return query
    return f"{query} {FOLLOWUP_QUERY_EXPANSION}"


def retrieve_query(
    message: str,
    history: Sequence[Dict[str, str]] | None = None,
) -> str:
    """Keep fever/wound context when the current turn is a short denial."""
    prior = [
        str(item.get("content") or "")
        for item in (history or [])
        if str(item.get("role") or "") in {"patient", "user"}
    ]
    combined = " ".join([*prior, message]).strip() or message
    return rewrite_followup_query(combined)


def candidate_pool_size(query: str, top_k: int) -> int:
    if rewrite_followup_query(query) == query:
        return top_k
    return max(top_k * CANDIDATE_POOL_FACTOR, top_k)


def followup_rank(chunk: KnowledgeChunk) -> int:
    blob = f"{chunk.title} {chunk.text}".lower()
    score = sum(HINT_MATCH_WEIGHT for hint in FOLLOWUP_DOC_HINTS if hint in blob)
    title = chunk.title.lower()
    if any(hint in title for hint in DIAGNOSIS_TITLE_HINTS) and "herida" not in blob:
        score -= DIAGNOSIS_TITLE_PENALTY
    return score


def rank_followup_hits(
    hits: list[KnowledgeChunk],
    query: str,
) -> list[KnowledgeChunk]:
    _ = query
    return sorted(hits, key=lambda hit: (followup_rank(hit), hit.score), reverse=True)


def prefer_unique_docs(hits: list[KnowledgeChunk], top_k: int) -> list[KnowledgeChunk]:
    unique: list[KnowledgeChunk] = []
    seen: set[str] = set()
    for hit in hits:
        if hit.doc_id in seen:
            continue
        seen.add(hit.doc_id)
        unique.append(hit)
        if len(unique) >= top_k:
            return unique
    for hit in hits:
        if len(unique) >= top_k:
            break
        if hit in unique:
            continue
        unique.append(hit)
    return unique


def select_citations(
    hits: list[KnowledgeChunk],
    query: str,
    top_k: int,
) -> list[KnowledgeChunk]:
    return prefer_unique_docs(rank_followup_hits(hits, query), top_k)
