from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class StartCallRequest(BaseModel):
    patient_name: str = "Paciente"
    procedure: str = "procedimiento_generico"
    language: str = "es"


class StartCallResponse(BaseModel):
    call_id: str
    greeting: str
    model_id: str


class ChatTurnRequest(BaseModel):
    call_id: str
    message: str


class CallMessage(BaseModel):
    role: str
    content: str
    sources: List[SourceCitation] = Field(default_factory=list)
    escalate: bool = False
    escalate_reason: Optional[str] = None
    patient_state: Optional[PatientState] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
    ended_at: datetime = Field(default_factory=datetime.utcnow)


class CallRecord(BaseModel):
    call_id: str
    patient_name: str
    procedure: str
    language: str = "es"
    status: str = "active"
    messages: List[CallMessage] = Field(default_factory=list)
    summary: Optional[CallSummary] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
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
