from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.agent.safety import severity_rank
from app.schemas import (
    AgentTurnResponse,
    CallMessage,
    CallRecord,
    CallSummary,
    Severity,
    SourceCitation,
    StartCallRequest,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CallService:
    def __init__(self, calls_path: Path) -> None:
        self.calls_path = calls_path
        self._calls: dict[str, CallRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.calls_path.exists():
            return
        raw = json.loads(self.calls_path.read_text(encoding="utf-8"))
        for item in raw:
            record = CallRecord(**item)
            self._calls[record.call_id] = record

    def _persist(self) -> None:
        payload = [c.model_dump(mode="json") for c in self._calls.values()]
        self.calls_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def start(self, req: StartCallRequest, greeting: str) -> CallRecord:
        call_id = str(uuid.uuid4())
        record = CallRecord(
            call_id=call_id,
            patient_name=req.patient_name,
            procedure=req.procedure,
            language=req.language,
            messages=[
                CallMessage(role="agent", content=greeting),
            ],
        )
        self._calls[call_id] = record
        self._persist()
        return record

    def get(self, call_id: str) -> CallRecord | None:
        return self._calls.get(call_id)

    def list_calls(self) -> list[CallRecord]:
        return sorted(self._calls.values(), key=lambda c: c.created_at, reverse=True)

    def append_user(self, call_id: str, message: str) -> CallRecord:
        record = self._require(call_id)
        record.messages.append(CallMessage(role="patient", content=message))
        self._persist()
        return record

    def append_agent(self, call_id: str, turn: AgentTurnResponse) -> CallRecord:
        record = self._require(call_id)
        record.messages.append(
            CallMessage(
                role="agent",
                content=turn.reply,
                sources=turn.sources,
                escalate=turn.escalate,
                escalate_reason=turn.escalate_reason,
                patient_state=turn.patient_state,
            )
        )
        self._persist()
        return record

    def end(self, call_id: str) -> CallRecord:
        record = self._require(call_id)
        symptoms: list[str] = []
        severity = Severity.none
        escalate = False
        escalate_reason = None
        sources_used: dict[str, SourceCitation] = {}

        for msg in record.messages:
            if msg.patient_state:
                for s in msg.patient_state.symptoms:
                    if s not in symptoms:
                        symptoms.append(s)
                if severity_rank(msg.patient_state.severity) > severity_rank(severity):
                    severity = msg.patient_state.severity
            if msg.escalate:
                escalate = True
                escalate_reason = msg.escalate_reason or escalate_reason
            for src in msg.sources:
                sources_used[src.chunk_id] = src

        summary_text = self._build_summary_text(
            record=record,
            symptoms=symptoms,
            severity=severity,
            escalate=escalate,
            escalate_reason=escalate_reason,
        )
        record.summary = CallSummary(
            call_id=record.call_id,
            patient_name=record.patient_name,
            procedure=record.procedure,
            symptoms=symptoms,
            severity=severity,
            escalate=escalate,
            escalate_reason=escalate_reason,
            sources_used=list(sources_used.values()),
            summary_text=summary_text,
            turn_count=len(record.messages),
            ended_at=_utcnow(),
        )
        record.status = "ended"
        record.ended_at = _utcnow()
        self._persist()
        return record

    def history_for_agent(self, call_id: str) -> list[dict[str, str]]:
        record = self._require(call_id)
        return [{"role": m.role, "content": m.content} for m in record.messages]

    def _require(self, call_id: str) -> CallRecord:
        record = self._calls.get(call_id)
        if not record:
            raise KeyError(call_id)
        return record

    def _build_summary_text(
        self,
        *,
        record: CallRecord,
        symptoms: list[str],
        severity: Severity,
        escalate: bool,
        escalate_reason: str | None,
    ) -> str:
        symptom_txt = ", ".join(symptoms) if symptoms else "ninguno reportado"
        alert = "SÍ" if escalate else "NO"
        reason = f" Motivo: {escalate_reason}." if escalate_reason else ""
        return (
            f"Llamada de seguimiento post-operatorio para {record.patient_name} "
            f"tras {record.procedure}. Síntomas: {symptom_txt}. "
            f"Severidad estimada: {severity.value}. Alerta a humano: {alert}.{reason}"
        )