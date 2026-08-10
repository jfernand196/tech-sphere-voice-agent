from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.api.deps import get_voice_service

router = APIRouter(prefix="/voice", tags=["voice"])


class TtsRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    engine: Optional[str] = Field(
        default=None,
        description="Server TTS engine: kokoro | piper (omit for auto).",
    )
    voice: Optional[str] = None
    speed: Optional[float] = Field(default=None, ge=0.6, le=1.4)


@router.get("/capabilities")
def capabilities():
    return get_voice_service().capabilities()


@router.post("/tts")
def synthesize_tts(body: TtsRequest):
    try:
        audio, content_type = get_voice_service().synthesize_tts(
            body.text,
            engine=body.engine,
            voice=body.voice,
            speed=body.speed,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}") from exc
    return Response(content=audio, media_type=content_type)
