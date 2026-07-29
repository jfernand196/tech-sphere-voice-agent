from fastapi import APIRouter

from app.api.deps import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    s = settings()
    return {
        "status": "ok",
        "model_id": s.model_id,
        "llm_provider": s.llm_provider,
    }
