"""Clinical safety / escalate rules (SRP: isolated from LLM orchestration)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.schemas import PatientState, Severity

ALARM_KEYWORDS: Dict[str, Severity] = {
    "no puedo respirar": Severity.severe,
    "dificultad para respirar": Severity.severe,
    "sangrado": Severity.severe,
    "sangrando": Severity.severe,
    "dolor intenso": Severity.severe,
    "dolor muy fuerte": Severity.severe,
    "fiebre": Severity.moderate,
    "39": Severity.severe,
    "40": Severity.severe,
    "desmayo": Severity.severe,
    "pecho": Severity.severe,
    "vómito": Severity.moderate,
    "vomito": Severity.moderate,
    "hablar con un humano": Severity.moderate,
    "quiero un doctor": Severity.moderate,
}


def severity_rank(value: Severity) -> int:
    order = {
        Severity.none: 0,
        Severity.mild: 1,
        Severity.moderate: 2,
        Severity.severe: 3,
    }
    return order.get(value, 0)


@dataclass(frozen=True)
class SafetyAssessment:
    symptoms: List[str]
    severity: Severity
    escalate: bool
    escalate_reason: Optional[str]


def assess_message(message: str) -> SafetyAssessment:
    lower = message.lower()
    symptoms: List[str] = []
    severity = Severity.mild if message.strip() else Severity.none
    escalate = False
    reason: Optional[str] = None

    for keyword, sev in ALARM_KEYWORDS.items():
        if keyword not in lower:
            continue
        symptoms.append(keyword)
        if severity_rank(sev) > severity_rank(severity):
            severity = sev
        if sev == Severity.severe or "humano" in keyword or "doctor" in keyword:
            escalate = True
            reason = f"Señal de alarma detectada: {keyword}"

    return SafetyAssessment(
        symptoms=symptoms,
        severity=severity,
        escalate=escalate,
        escalate_reason=reason,
    )


def apply_safety_overrides(
    message: str,
    *,
    escalate: bool,
    escalate_reason: Optional[str],
    patient_state: PatientState,
) -> Tuple[bool, Optional[str], PatientState]:
    """Post-LLM guardrail: never trust the model alone for severe alarms."""
    assessment = assess_message(message)
    if assessment.escalate and assessment.severity == Severity.severe:
        escalate = True
        escalate_reason = escalate_reason or assessment.escalate_reason
        patient_state.severity = Severity.severe
        for symptom in assessment.symptoms:
            if symptom not in patient_state.symptoms:
                patient_state.symptoms.append(symptom)
    return escalate, escalate_reason, patient_state
