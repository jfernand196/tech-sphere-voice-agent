from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Severity(str, Enum):
    none = "none"
    mild = "mild"
    moderate = "moderate"
    severe = "severe"


class SourceCitation(BaseModel):
    doc_id: str
    title: str
    chunk_id: str
    excerpt: Optional[str] = None


class PatientState(BaseModel):
    symptoms: List[str] = Field(default_factory=list)
    severity: Severity = Severity.none
    notes: Optional[str] = None


class AgentTurnResponse(BaseModel):
    """Contract every agent turn must satisfy (traceability + escalate)."""

    reply: str
    sources: List[SourceCitation] = Field(default_factory=list)
    patient_state: PatientState = Field(default_factory=PatientState)
    escalate: bool = False
    escalate_reason: Optional[str] = None
    model_id: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    model_invocations: int = 1
    rag_queries: int = 1


class StartCallRequest(BaseModel):
    patient_name: str = "Paciente"
    procedure: str = "procedimiento_generico"
    dia_postop: int = Field(default=1, ge=0, le=60)
    language: str = "es"


class DemoPatient(BaseModel):
    """Curated case for the call UI selector (from official kit Excels)."""

    id: str
    paciente_id: str
    nombre: str
    procedimiento: str
    dia_postop: int
    label: str
    demo_hint: str = ""
    ciudad: str = ""
    eps: str = ""


class StartCallResponse(BaseModel):
    call_id: str
    greeting: str
    model_id: str


class ChatTurnRequest(BaseModel):
    call_id: str
    message: str


class EndCallRequest(BaseModel):
    """Optional client-measured voice→voice latencies (ms) for challenge P50/P95."""

    e2e_latency_ms: List[int] = Field(default_factory=list)


class CallMessage(BaseModel):
    role: str
    content: str
    sources: List[SourceCitation] = Field(default_factory=list)
    escalate: bool = False
    escalate_reason: Optional[str] = None
    patient_state: Optional[PatientState] = None
    latency_ms: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    model_invocations: Optional[int] = None
    rag_queries: Optional[int] = None
    created_at: datetime = Field(default_factory=_utc_now)


class CallSummary(BaseModel):
    call_id: str
    patient_name: str
    procedure: str
    symptoms: List[str]
    severity: Severity
    escalate: bool
    escalate_reason: Optional[str]
    sources_used: List[SourceCitation]
    summary_text: str
    turn_count: int
    ended_at: datetime = Field(default_factory=_utc_now)
    # Challenge metrics (§5)
    tokens_in_total: int = 0
    tokens_out_total: int = 0
    model_invocations_total: int = 0
    rag_queries_total: int = 0
    agent_latency_p50_ms: Optional[int] = None
    agent_latency_p95_ms: Optional[int] = None
    e2e_latency_p50_ms: Optional[int] = None
    e2e_latency_p95_ms: Optional[int] = None
    cost_usd_estimate: Optional[float] = None
    cost_note: Optional[str] = None


class CallRecord(BaseModel):
    call_id: str
    patient_name: str
    procedure: str
    dia_postop: int = 1
    language: str = "es"
    status: str = "active"
    messages: List[CallMessage] = Field(default_factory=list)
    summary: Optional[CallSummary] = None
    created_at: datetime = Field(default_factory=_utc_now)
    ended_at: Optional[datetime] = None


class DocumentInfo(BaseModel):
    doc_id: str
    title: str
    filename: str
    chunk_count: int
    created_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeQueryRequest(BaseModel):
    query: str
    top_k: int = 4


class KnowledgeChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    text: str
    score: float
