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
    "dolor lo pondría en 8": Severity.severe,
    "dolor lo pondría en 9": Severity.severe,
    "dolor lo pondría en 10": Severity.severe,
    "/10": Severity.mild,  # presence alone is weak; composites handle risk
    "fiebre": Severity.moderate,
    "afiebrad": Severity.moderate,
    "cuerpo caliente": Severity.moderate,
    "38": Severity.moderate,
    "39": Severity.severe,
    "40": Severity.severe,
    "desmayo": Severity.severe,
    "pecho": Severity.severe,
    "vómito": Severity.moderate,
    "vomito": Severity.moderate,
    "secreción purulenta": Severity.severe,
    "secrecion purulenta": Severity.severe,
    "pus": Severity.severe,
    "líquido amarillo": Severity.severe,
    "liquido amarillo": Severity.severe,
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


def _has_fever_signal(lower: str) -> bool:
    return any(
        token in lower
        for token in ("fiebre", "afiebrad", "cuerpo caliente", "38", "39", "40")
    )


def _has_wound_infection_signal(lower: str) -> bool:
    return any(
        token in lower
        for token in (
            "secreción purulenta",
            "secrecion purulenta",
            "pus",
            "líquido amarillo",
            "liquido amarillo",
            "secreción",
            "secrecion",
        )
    )


def _high_pain(lower: str) -> bool:
    for n in ("8/10", "9/10", "10/10", "en 8/", "en 9/", "en 10/"):
        if n in lower.replace(" ", ""):
            return True
    return "dolor intenso" in lower or "dolor muy fuerte" in lower


def assess_message(message: str) -> SafetyAssessment:
    lower = message.lower()
    symptoms: List[str] = []
    severity = Severity.mild if message.strip() else Severity.none
    escalate = False
    reason: Optional[str] = None

    for keyword, sev in ALARM_KEYWORDS.items():
        if keyword == "/10":
            continue
        if keyword not in lower:
            continue
        symptoms.append(keyword)
        if severity_rank(sev) > severity_rank(severity):
            severity = sev
        if sev == Severity.severe or "humano" in keyword or "doctor" in keyword:
            escalate = True
            reason = f"Señal de alarma detectada: {keyword}"

    # Composite clinical picture (common in rojo trajectories).
    if _has_fever_signal(lower) and _has_wound_infection_signal(lower):
        escalate = True
        severity = Severity.severe
        reason = reason or "Fiebre + signos de infección en la herida"
        symptoms.append("fiebre+herida")
    elif _high_pain(lower) and _has_fever_signal(lower):
        escalate = True
        if severity_rank(Severity.severe) > severity_rank(severity):
            severity = Severity.severe
        reason = reason or "Dolor alto + fiebre"
        symptoms.append("dolor+fiebre")

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
    """Post-LLM guardrail: never trust the model alone for alarm signals."""
    assessment = assess_message(message)
    if assessment.escalate:
        escalate = True
        escalate_reason = escalate_reason or assessment.escalate_reason
        if severity_rank(assessment.severity) > severity_rank(patient_state.severity):
            patient_state.severity = assessment.severity
        for symptom in assessment.symptoms:
            if symptom not in patient_state.symptoms:
                patient_state.symptoms.append(symptom)
    return escalate, escalate_reason, patient_state
