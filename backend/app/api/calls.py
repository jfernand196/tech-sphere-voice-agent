from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Body, HTTPException

from app.api.deps import get_agent_service, get_call_service, settings
from app.schemas import (
    AgentTurnResponse,
    CallSummary,
    ChatTurnRequest,
    EndCallRequest,
    StartCallRequest,
    StartCallResponse,
)

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/start", response_model=StartCallResponse)
async def start_call(body: StartCallRequest):
    day = body.dia_postop
    day_phrase = f"en el día {day} después de tu {body.procedure}"
    greeting = (
        f"Hola {body.patient_name}, te llamo para tu seguimiento {day_phrase}. "
        f"¿Cómo te sientes en este momento?"
    )
    record = get_call_service().start(body, greeting=greeting)
    return StartCallResponse(
        call_id=record.call_id,
        greeting=greeting,
        model_id=settings().model_id,
    )


@router.post("/{call_id}/turn", response_model=AgentTurnResponse)
async def chat_turn(call_id: str, body: ChatTurnRequest):
    if body.call_id != call_id:
        raise HTTPException(status_code=400, detail="call_id mismatch")
    calls = get_call_service()
    record = calls.get(call_id)
    if not record:
        raise HTTPException(status_code=404, detail="Call not found")
    if record.status != "active":
        raise HTTPException(status_code=400, detail="Call already ended")

    calls.append_user(call_id, body.message)
    history = calls.history_for_agent(call_id)
    turn = await get_agent_service().respond(
        patient_name=record.patient_name,
        procedure=record.procedure,
        dia_postop=record.dia_postop,
        message=body.message,
        history=history[:-1],
    )
    calls.append_agent(call_id, turn)
    return turn


@router.post("/{call_id}/end", response_model=CallSummary)
def end_call(
    call_id: str,
    body: Optional[EndCallRequest] = Body(default=None),
):
    # Optional[…] required for FastAPI on Python 3.9 (X | None breaks route parsing).
    calls = get_call_service()
    if not calls.get(call_id):
        raise HTTPException(status_code=404, detail="Call not found")
    payload = body or EndCallRequest()
    record = calls.end(call_id, e2e_latency_ms=payload.e2e_latency_ms)
    assert record.summary is not None
    return record.summary
