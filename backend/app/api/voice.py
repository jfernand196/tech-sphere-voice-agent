from fastapi import APIRouter, File, UploadFile

from app.api.deps import get_voice_service

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/capabilities")
def capabilities():
    return get_voice_service().capabilities()


@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    content = await file.read()
    return await get_voice_service().transcribe_audio(
        content, filename=file.filename or "audio.webm"
    )
