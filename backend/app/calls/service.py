from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.agent.safety import severity_rank
from app.metrics import rollup_call_metrics
from app.schemas import (
    AgentTurnResponse,
    CallMessage,
    CallRecord,
    CallSummary,
    Severity,
    SourceCitation,
    StartCallRequest,
)
from app.timeutil import utc_now


def agent_message_from_turn(turn: AgentTurnResponse) -> CallMessage:
    """Map turn DTO → persisted message (single mapping site)."""
    return CallMessage(
        role="agent",
        content=turn.reply,
        sources=turn.sources,
        escalate=turn.escalate,
        escalate_reason=turn.escalate_reason,
        patient_state=turn.patient_state,
        latency_ms=turn.latency_ms,
        tokens_in=turn.tokens_in,
        tokens_out=turn.tokens_out,
        model_invocations=turn.model_invocations,
        rag_queries=turn.rag_queries,
    )


@dataclass
class _ClinicalFold:
    symptoms: list[str]
    severity: Severity
    escalate: bool
    escalate_reason: str | None
    sources_used: list[SourceCitation]


def _fold_clinical(messages: list[CallMessage]) -> _ClinicalFold:
    symptoms: list[str] = []
    severity = Severity.none
    escalate = False
    escalate_reason: str | None = None
    sources_used: dict[str, SourceCitation] = {}

    for msg in messages:
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

    return _ClinicalFold(
        symptoms=symptoms,
        severity=severity,
        escalate=escalate,
        escalate_reason=escalate_reason,
        sources_used=list(sources_used.values()),
    )


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
            dia_postop=req.dia_postop,
            language=req.language,
            messages=[CallMessage(role="agent", content=greeting)],
        )
        self._calls[call_id] = record
        self._persist()
        return record

    def get(self, call_id: str) -> CallRecord | None:
        return self._calls.get(call_id)

    def append_user(self, call_id: str, message: str) -> CallRecord:
        record = self._require(call_id)
        record.messages.append(CallMessage(role="patient", content=message))
        self._persist()
        return record

    def append_agent(self, call_id: str, turn: AgentTurnResponse) -> CallRecord:
        record = self._require(call_id)
        record.messages.append(agent_message_from_turn(turn))
        self._persist()
        return record

    def end(self, call_id: str, *, e2e_latency_ms: list[int] | None = None) -> CallRecord:
        record = self._require(call_id)
        clinical = _fold_clinical(record.messages)
        metrics = rollup_call_metrics(record.messages, e2e_latency_ms)

        record.summary = CallSummary(
            call_id=record.call_id,
            patient_name=record.patient_name,
            procedure=record.procedure,
            symptoms=clinical.symptoms,
            severity=clinical.severity,
            escalate=clinical.escalate,
            escalate_reason=clinical.escalate_reason,
            sources_used=clinical.sources_used,
            summary_text=_summary_text(record, clinical),
            turn_count=metrics.patient_turns,
            ended_at=utc_now(),
            tokens_in_total=metrics.tokens_in_total,
            tokens_out_total=metrics.tokens_out_total,
            model_invocations_total=metrics.model_invocations_total,
            rag_queries_total=metrics.rag_queries_total,
            agent_latency_p50_ms=metrics.agent_latency_p50_ms,
            agent_latency_p95_ms=metrics.agent_latency_p95_ms,
            e2e_latency_p50_ms=metrics.e2e_latency_p50_ms,
            e2e_latency_p95_ms=metrics.e2e_latency_p95_ms,
            cost_usd_estimate=metrics.cost_usd_estimate,
            cost_note=metrics.cost_note,
        )
        record.status = "ended"
        record.ended_at = utc_now()
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


def _summary_text(record: CallRecord, clinical: _ClinicalFold) -> str:
    symptom_txt = ", ".join(clinical.symptoms) if clinical.symptoms else "ninguno reportado"
    alert = "SÍ" if clinical.escalate else "NO"
    reason = f" Motivo: {clinical.escalate_reason}." if clinical.escalate_reason else ""
    return (
        f"Llamada de seguimiento post-operatorio para {record.patient_name} "
        f"tras {record.procedure}. Síntomas: {symptom_txt}. "
        f"Severidad estimada: {clinical.severity.value}. Alerta a humano: {alert}.{reason}"
    )
