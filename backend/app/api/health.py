from fastapi import APIRouter

from app.agent.factory import describe_llm
from app.api.deps import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    s = settings()
    info = describe_llm(s)
    return {
        "status": "ok" if info["llm_ready"] else "degraded",
        **info,
    }
