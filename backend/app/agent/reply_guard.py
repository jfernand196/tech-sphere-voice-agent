"""Post-LLM spoken-reply guards (SRP: not clinical scoring, not RAG)."""

from __future__ import annotations

import re

SPOKEN_ALERT_SENTENCE = (
    "Voy a marcar una alerta para que un humano revise tu caso."
)
SPOKEN_WATCH_PLAN = (
    "Vigila falta de aire, sangrado que empapa o fiebre que sube; "
    "si empeora, ve a urgencias."
)
HOME_WATCH_WITHOUT_ALERT = (
    "Sigue el analgésico indicado, hidrátate y avísame si aparece "
    "fiebre de 38.5 o más, pus en la herida o falta de aire."
)

_ALERT_MARKERS = (
    "voy a marcar una alerta",
    "marcar una alerta",
    "alerta para que un humano",
    "alertar a personal",
    "alertar a un humano",
    "voy a alertar",
    "marco revisión humana",
    "marco revision humana",
    "revisión humana",
    "revision humana",
    "voy a comunicar",
    "comunicar su situación",
    "profesional de salud",
    "un profesional de salud",
    "personal de salud",
)

_PLAN_MARKERS = (
    "vigila falta de aire",
    "sangrado que empapa",
    "ve a urgencias",
    "acuda a urgencias",
    "hasta que te contacten",
)

_UNWARRANTED_ALERT_MARKERS = (
    "voy a comunicar",
    "comunicar su situación",
    "profesional de salud",
    "un profesional de salud",
    "personal de salud",
    "voy a marcar una alerta",
    "voy a alertar",
    "alertar a un humano",
    "alertar a personal",
    "acuda a urgencias",
    "ve a urgencias",
)


def reply_already_speaks_alert(reply: str) -> bool:
    lower = (reply or "").lower()
    return any(marker in lower for marker in _ALERT_MARKERS)


def reply_already_has_watch_plan(reply: str) -> bool:
    lower = (reply or "").lower()
    return any(marker in lower for marker in _PLAN_MARKERS)


def _append_sentence(text: str, sentence: str) -> str:
    body = (text or "").strip()
    if not body:
        return sentence
    if body[-1] not in ".!?…":
        body = f"{body}."
    return f"{body} {sentence}"


def ensure_spoken_alert(reply: str, escalate: bool) -> str:
    """If safety escalated, the patient must hear the alert and a short watch plan."""
    text = (reply or "").strip()
    if not escalate:
        return text
    if not reply_already_speaks_alert(text):
        text = _append_sentence(text, SPOKEN_ALERT_SENTENCE)
    if not reply_already_has_watch_plan(text):
        text = _append_sentence(text, SPOKEN_WATCH_PLAN)
    return text


def drop_unwarranted_alert_close(reply: str) -> str:
    """Remove Gemini's false handoff when safety cancelled escalate."""
    text = (reply or "").strip()
    if not text:
        return text
    parts = re.split(r"(?<=[.!?…])\s+", text)
    kept = [
        part
        for part in parts
        if not any(marker in part.lower() for marker in _UNWARRANTED_ALERT_MARKERS)
    ]
    dropped = len(kept) != len(parts)
    out = " ".join(kept).strip()
    if not dropped:
        return text
    if not out:
        return HOME_WATCH_WITHOUT_ALERT
    if HOME_WATCH_WITHOUT_ALERT.lower() not in out.lower():
        return _append_sentence(out, HOME_WATCH_WITHOUT_ALERT)
    return out
