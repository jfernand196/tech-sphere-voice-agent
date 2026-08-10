from fastapi import APIRouter

from app.agent.factory import describe_llm
from app.api.deps import get_knowledge_service, settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    s = settings()
    info = describe_llm(s)
    rag = get_knowledge_service().index_stats()
    llm_ok = bool(info["llm_ready"])
    rag_ok = bool(rag["rag_ok"])
    status = "ok" if llm_ok and rag_ok else "degraded"
    detail_parts = []
    if not llm_ok:
        detail_parts.append(info.get("llm_detail") or "LLM no listo")
    if not rag_ok:
        detail_parts.append(
            f"RAG vacío: {rag['rag_docs']} doc(s) sin vectores "
            f"(chunks={rag['rag_chunks']}); reinicia o re-ingiere"
        )
    return {
        "status": status,
        **info,
        **rag,
        "health_detail": " · ".join(detail_parts) if detail_parts else info.get("llm_detail"),
    }
