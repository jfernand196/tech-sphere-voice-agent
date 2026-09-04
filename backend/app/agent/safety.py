"""Clinical safety / escalate rules (SRP: isolated from LLM orchestration)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from app.schemas import PatientState, Severity

FEVER_TOKENS: Tuple[str, ...] = (
    "fiebre",
    "afiebrad",
    "cuerpo caliente",
    "38",
    "39",
    "40",
)
WOUND_INFECTION_TOKENS: Tuple[str, ...] = (
    "secreción purulenta",
    "secrecion purulenta",
    "pus",
    "líquido amarillo",
    "liquido amarillo",
    "secreción",
    "secrecion",
)
WOUND_CARE_TOKENS: Tuple[str, ...] = ("herida", "puntos")
BLEEDING_TOKENS: Tuple[str, ...] = ("sangrado", "sangrando")
RESPIRATORY_TOKENS: Tuple[str, ...] = (
    "no puedo respirar",
    "dificultad para respirar",
    "respir",
    "pecho",
)
HIGH_FEVER_RE = re.compile(
    r"39|40|38\s*[.,]\s*[5-9]|38\s+con\s+[5-9]|38\s*[5-9]"
)
_CLAUSE_SPLIT = re.compile(
    r"\s+(?:y|pero|aunque|sino(?:\s+que)?)\s+",
    re.IGNORECASE,
)
_UNCERTAIN_NOT_DENIAL = re.compile(r"\bno\s+s[eé]\s+si\b")
_NOT_ONLY = re.compile(r"\bno\s+solo\b")
_CANT_BREATHE_PREFIX = re.compile(r"no\s+puedo\s+$")
_DENIAL_CUE = re.compile(
    r"\b(?:no|tampoco|sin|ni|nunca|jamás|jamas|ningún|ningun|ninguna|ninguno)\b"
)
# The phrase itself is the alarm, not a denial of breathing.
_SELF_ALARM_KEYWORDS = frozenset(
    {"no puedo respirar", "dificultad para respirar"}
)


def _clause_before(text: str, start: int) -> str:
    prefix = text[:start]
    parts = _CLAUSE_SPLIT.split(prefix)
    return parts[-1] if parts else prefix


def mention_is_affirmed(text: str, token: str, start: int) -> bool:
    """False when the token sits in a denied clause (no / tampoco / sin …)."""
    if token in _SELF_ALARM_KEYWORDS:
        return True
    clause = _clause_before(text, start)
    if token.startswith("respir") and _CANT_BREATHE_PREFIX.search(clause):
        return True
    if _UNCERTAIN_NOT_DENIAL.search(clause) or _NOT_ONLY.search(clause):
        return True
    return not _DENIAL_CUE.search(clause)


def contains_affirmed(text: str, token: str) -> bool:
    """True if `token` appears at least once outside a Spanish denial clause."""
    if not token:
        return False
    lower = text.lower()
    start = 0
    while True:
        idx = lower.find(token, start)
        if idx < 0:
            return False
        if mention_is_affirmed(lower, token, idx):
            return True
        start = idx + max(len(token), 1)


def _contains_any(text: str, tokens: Sequence[str], *, affirmed: bool = False) -> bool:
    lower = text.lower()
    if affirmed:
        return any(contains_affirmed(lower, token) for token in tokens)
    return any(token in lower for token in tokens)


def has_fever_signal(text: str) -> bool:
    return _contains_any(text, FEVER_TOKENS, affirmed=True)


def has_wound_infection_signal(text: str) -> bool:
    return _contains_any(text, WOUND_INFECTION_TOKENS, affirmed=True)


def has_wound_mention(text: str) -> bool:
    return has_wound_infection_signal(text) or _contains_any(text, WOUND_CARE_TOKENS)


def wants_wound_followup(query: str) -> bool:
    return has_fever_signal(query) or has_wound_mention(query)


def is_high_fever(text: str) -> bool:
    return bool(HIGH_FEVER_RE.search(text.lower()))


_STATED_TEMP_RE = re.compile(
    r"3[7-9]\s*[.,]\s*\d|3[7-9]\s+grados|\b3[7-9]\b|\b40\b"
)


def has_stated_temperature(text: str) -> bool:
    """Patient already gave a thermometer reading (e.g. 37,4)."""
    return bool(_STATED_TEMP_RE.search((text or "").lower()))


def fever_word(text: str) -> str:
    return "fiebre alta" if is_high_fever(text) else "fiebre"


def has_bleeding_signal(text: str) -> bool:
    return _contains_any(text, BLEEDING_TOKENS, affirmed=True)


def has_respiratory_signal(text: str) -> bool:
    return _contains_any(text, RESPIRATORY_TOKENS, affirmed=True)


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


def _high_pain(lower: str) -> bool:
    compact = lower.replace(" ", "")
    if any(n in compact for n in ("8/10", "9/10", "10/10", "en 8/", "en 9/", "en 10/")):
        return True
    return contains_affirmed(lower, "dolor intenso") or contains_affirmed(
        lower, "dolor muy fuerte"
    )


def assess_message(message: str) -> SafetyAssessment:
    lower = message.lower()
    symptoms: List[str] = []
    severity = Severity.mild if message.strip() else Severity.none
    escalate = False
    reason: Optional[str] = None

    for keyword, sev in ALARM_KEYWORDS.items():
        if keyword == "/10":
            continue
        if not contains_affirmed(lower, keyword):
            continue
        symptoms.append(keyword)
        if severity_rank(sev) > severity_rank(severity):
            severity = sev
        if sev == Severity.severe or "humano" in keyword or "doctor" in keyword:
            escalate = True
            reason = f"Señal de alarma detectada: {keyword}"

    # Composite clinical picture (common in rojo trajectories).
    if has_fever_signal(lower) and has_wound_infection_signal(lower):
        escalate = True
        severity = Severity.severe
        reason = "Fiebre + signos de infección en la herida"
        symptoms.append("fiebre+herida")
    elif _high_pain(lower) and has_fever_signal(lower):
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


_PROBE_DENIAL_MARKERS: Tuple[str, ...] = (
    "no he notado",
    "no he tenido",
    "no he visto",
    "por el momento no",
    "por ahora no",
    "nada de eso",
    "ninguno de esos",
    "ninguna de esas",
    "tampoco está",
    "tampoco esta",
    "no está saliendo",
    "no esta saliendo",
    "no hay pus",
    "sin pus",
    "no tiene pus",
    "no sale pus",
)

_SHORT_DENIALS = frozenset(
    {
        "no",
        "no.",
        "nop",
        "para nada",
        "ninguno",
        "ninguna",
        "tampoco",
        "tampoco.",
    }
)


def is_probe_denial(message: str) -> bool:
    """Patient is answering 'no' to the symptoms the agent just asked about."""
    lower = (message or "").lower().strip()
    if not lower:
        return False
    if (
        has_respiratory_signal(lower)
        or has_bleeding_signal(lower)
        or has_wound_infection_signal(lower)
        or is_high_fever(lower)
        or _high_pain(lower)
    ):
        return False
    if lower in _SHORT_DENIALS:
        return True
    return any(marker in lower for marker in _PROBE_DENIAL_MARKERS)


def patient_conversation_text(
    message: str,
    history: Sequence[Dict[str, str]] | None = None,
) -> str:
    prior = [
        str(item.get("content") or "")
        for item in (history or [])
        if str(item.get("role") or "") in {"patient", "user"}
    ]
    return " ".join([*prior, message]).strip()


# Internal detector tokens → labels a clinician can read on hang-up.
_SYMPTOM_ALIASES: Dict[str, str] = {
    "38": "fiebre",
    "39": "fiebre",
    "40": "fiebre",
    "afiebrad": "fiebre",
    "cuerpo caliente": "fiebre",
    "fiebre+herida": "secreción",
    "dolor+fiebre": "dolor",
    "secrecion purulenta": "secreción purulenta",
    "secreción": "secreción",
    "secrecion": "secreción",
    "pus": "secreción",
    "líquido amarillo": "secreción",
    "liquido amarillo": "secreción",
    "no puedo respirar": "falta de aire",
    "dificultad para respirar": "falta de aire",
    "sangrando": "sangrado",
    "dolor intenso": "dolor",
    "dolor muy fuerte": "dolor",
    "dolor lo pondría en 8": "dolor",
    "dolor lo pondría en 9": "dolor",
    "dolor lo pondría en 10": "dolor",
}

_SKIP_SYMPTOM_KEYS = frozenset({"hablar con un humano", "quiero un doctor", "/10"})


def humanize_symptom(raw: str) -> Optional[str]:
    """Map detector tokens (38, fiebre+herida) to Spanish a clinician can read."""
    key = (raw or "").strip()
    if not key:
        return None
    lowered = key.lower()
    if lowered in _SKIP_SYMPTOM_KEYS:
        return None
    if lowered in _SYMPTOM_ALIASES:
        return _SYMPTOM_ALIASES[lowered]
    if lowered.replace(".", "", 1).isdigit() and lowered.startswith(("37", "38", "39", "40")):
        return "fiebre"
    return key


def humanize_symptoms(items: Sequence[str]) -> List[str]:
    """Dedupe hang-up chips; keep the more specific label when one contains another."""
    mapped: List[str] = []
    seen: set[str] = set()
    for item in items:
        label = humanize_symptom(item)
        if not label:
            continue
        key = label.lower()
        if key in seen:
            continue
        seen.add(key)
        mapped.append(label)

    dropped = {
        label.lower()
        for label in mapped
        if any(
            other.lower() != label.lower()
            and label.lower() in other.lower()
            for other in mapped
        )
    }
    return [label for label in mapped if label.lower() not in dropped]


def apply_safety_overrides(
    message: str,
    *,
    escalate: bool,
    escalate_reason: Optional[str],
    patient_state: PatientState,
    history: Sequence[Dict[str, str]] | None = None,
) -> Tuple[bool, Optional[str], PatientState]:
    """Post-LLM guardrail: never miss an alarm; drop LLM escalate on a clean denial."""
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

    if escalate and is_probe_denial(message):
        picture = assess_message(patient_conversation_text(message, history))
        if not picture.escalate:
            return False, None, patient_state
    return escalate, escalate_reason, patient_state
