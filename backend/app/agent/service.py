from __future__ import annotations

import json
import re
import time
from typing import Any

import httpx

from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt
from app.config import Settings
from app.rag.service import KnowledgeService
from app.schemas import (
    AgentTurnResponse,
    PatientState,
    Severity,
    SourceCitation,
)


ALARM_KEYWORDS = {
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


def _severity_rank(value: Severity) -> int:
    order = {
        Severity.none: 0,
        Severity.mild: 1,
        Severity.moderate: 2,
        Severity.severe: 3,
    }
    return order.get(value, 0)


def _clean_excerpt(text: str, limit: int = 160) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    cut = cleaned[:limit].rsplit(" ", 1)[0]
    return f"{cut}…"


def _compose_clinical_reply(
    *,
    message: str,
    severity: Severity,
    escalate: bool,
    doc_title: str,
    context_text: str,
) -> str:
    """Natural spoken reply for mock mode. Sources stay in the JSON, not pasted raw."""
    ctx = context_text.lower()

    if "respir" in message or "pecho" in message:
        return (
            f"Entiendo, eso suena urgente. Según {doc_title}, la dificultad para respirar "
            "o el dolor en el pecho son signos de alarma. Quédate en un lugar seguro; "
            "voy a alertar a personal capacitado ahora mismo."
        )

    if "sangr" in message:
        return (
            f"Gracias por avisarme. En {doc_title} el sangrado abundante se considera "
            "signo de alarma. ¿La sangre empapa apósitos con rapidez o solo hay un poco "
            "en la gasa? Mientras tanto marco revisión humana."
            if escalate
            else (
                f"Anoto el sangrado. Según {doc_title}, necesitamos saber si es abundante. "
                "¿Cuántas gasas has cambiado en la última hora?"
            )
        )

    if "fiebre" in message or re.search(r"3[89]|40", message):
        high = bool(re.search(r"38\.[5-9]|39|40", message)) or "39" in message or "40" in message
        if high or escalate:
            return (
                f"Escucho que tienes fiebre alta. Según {doc_title}, si supera 38.5 °C "
                "o no cede, debemos alertar a un humano. ¿Llevas más de unas horas así "
                "y tienes escalofríos o malestar fuerte?"
            )
        guidance = (
            "hidratación, reposo relativo y reevaluación en la siguiente hora"
            if "hidratación" in ctx or "hidratacion" in ctx
            else "reposo, líquidos y seguimiento cercano"
        )
        return (
            f"Gracias por contármelo. Con fiebre leve, {doc_title} sugiere {guidance}. "
            "¿Desde cuándo la tienes y qué temperatura exacta marcó el termómetro? "
            "También dime si hay escalofríos, vómito o dolor fuerte."
        )

    if "herida" in message or "secrec" in message or "pus" in message or "puntos" in message:
        return (
            f"Entiendo lo de la herida. Según {doc_title}, el enrojecimiento leve puede "
            "ser esperado al inicio, pero secreción purulenta, mal olor o apertura de puntos "
            "requieren alerta. ¿Ves pus, mal olor o se abrió algún punto? "
            "En una escala del 1 al 10, ¿qué tan mal te sientes?"
        )

    if "dolor" in message:
        return (
            f"Lamento que estés con dolor. {doc_title} indica cumplir el esquema de "
            "analgésicos y escalar si el dolor es intenso o no cede. "
            "Del 1 al 10, ¿qué tan fuerte es ahora y ya tomaste la medicación indicada?"
        )

    if "vómito" in message or "vomito" in message:
        return (
            f"Anoto el vómito. En {doc_title}, si es persistente e impide tomar líquidos, "
            "hay que alertar. ¿Has podido retener agua o suero en las últimas horas?"
        )

    return (
        f"Gracias, te escucho. Me estoy basando en {doc_title} para orientarte sin inventar "
        "indicaciones. Cuéntame el síntoma principal, desde cuándo lo tienes y "
        "qué tan intenso es del 1 al 10."
    )



class AgentService:
    def __init__(self, settings: Settings, knowledge: KnowledgeService) -> None:
        self.settings = settings
        self.knowledge = knowledge

    async def respond(
        self,
        *,
        patient_name: str,
        procedure: str,
        message: str,
        history: list[dict[str, str]],
    ) -> AgentTurnResponse:
        started = time.perf_counter()
        rag_hits = self.knowledge.retrieve(message, top_k=4)
        rag_context = [h.model_dump() for h in rag_hits]

        if self.settings.llm_provider == "anthropic" and self.settings.anthropic_api_key:
            raw = await self._call_anthropic(
                patient_name=patient_name,
                procedure=procedure,
                message=message,
                history=history,
                rag_context=rag_context,
            )
            parsed = self._parse_json_response(raw)
        else:
            parsed = self._mock_respond(message=message, rag_context=rag_context)

        sources = self._build_sources(parsed, rag_hits)
        escalate, reason, state = self._apply_safety_rules(message, parsed)

        latency_ms = int((time.perf_counter() - started) * 1000)
        return AgentTurnResponse(
            reply=str(parsed.get("reply") or "¿Me puedes contar un poco más cómo te sientes?"),
            sources=sources,
            patient_state=state,
            escalate=escalate,
            escalate_reason=reason,
            model_id=self.settings.model_id,
            latency_ms=latency_ms,
        )

    async def _call_anthropic(
        self,
        *,
        patient_name: str,
        procedure: str,
        message: str,
        history: list[dict[str, str]],
        rag_context: list[dict],
    ) -> str:
        user_prompt = build_user_prompt(
            patient_name=patient_name,
            procedure=procedure,
            message=message,
            history=history,
            rag_context=rag_context,
        )
        payload = {
            "model": self.settings.model_id,
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        }
        headers = {
            "x-api-key": self.settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
        parts = data.get("content") or []
        return "".join(p.get("text", "") for p in parts if p.get("type") == "text")

    def _parse_json_response(self, raw: str) -> dict[str, Any]:
        raw = raw.strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
        return {
            "reply": raw or "No pude interpretar la respuesta del modelo.",
            "sources": [],
            "patient_state": {"symptoms": [], "severity": "none"},
            "escalate": False,
            "escalate_reason": None,
        }

    def _mock_respond(self, *, message: str, rag_context: list[dict]) -> dict[str, Any]:
        lower = message.lower()
        escalate = False
        reason = None
        severity = Severity.mild
        symptoms: list[str] = []

        for keyword, sev in ALARM_KEYWORDS.items():
            if keyword in lower:
                symptoms.append(keyword)
                if _severity_rank(sev) > _severity_rank(severity):
                    severity = sev
                if sev == Severity.severe or "humano" in keyword or "doctor" in keyword:
                    escalate = True
                    reason = f"Señal de alarma detectada: {keyword}"

        sources = [
            {
                "doc_id": c["doc_id"],
                "title": c["title"],
                "chunk_id": c["chunk_id"],
                "excerpt": _clean_excerpt(c["text"]),
            }
            for c in rag_context[:2]
        ]

        if rag_context:
            reply = _compose_clinical_reply(
                message=lower,
                severity=severity,
                escalate=escalate,
                doc_title=rag_context[0]["title"],
                context_text=" ".join(c["text"] for c in rag_context[:2]),
            )
        else:
            reply = (
                "No tengo en mi base de conocimiento un protocolo que cubra exactamente eso. "
                "Prefiero no inventar indicaciones clínicas. "
                "¿Quieres que alerte a personal capacitado?"
            )
            if any(k in lower for k in ("dolor", "fiebre", "sangre", "vómito", "vomito")):
                escalate = True
                reason = reason or "Síntoma sin respaldo documental suficiente"

        if escalate and "alerta" not in reply.lower():
            reply += " Voy a marcar una alerta para que un humano revise tu caso."

        return {
            "reply": reply,
            "sources": sources,
            "patient_state": {
                "symptoms": symptoms or (["malestar"] if message.strip() else []),
                "severity": severity.value,
                "notes": message[:200],
            },
            "escalate": escalate,
            "escalate_reason": reason,
        }

    def _build_sources(self, parsed: dict[str, Any], rag_hits) -> list[SourceCitation]:
        sources: list[SourceCitation] = []
        raw_sources = parsed.get("sources") or []
        if raw_sources:
            for item in raw_sources:
                try:
                    sources.append(SourceCitation(**item))
                except Exception:
                    continue
        if not sources:
            for hit in rag_hits[:2]:
                sources.append(
                    SourceCitation(
                        doc_id=hit.doc_id,
                        title=hit.title,
                        chunk_id=hit.chunk_id,
                        excerpt=hit.text[:160],
                    )
                )
        return sources

    def _apply_safety_rules(
        self, message: str, parsed: dict[str, Any]
    ) -> tuple[bool, str | None, PatientState]:
        state_raw = parsed.get("patient_state") or {}
        try:
            state = PatientState(**state_raw)
        except Exception:
            state = PatientState(symptoms=[], severity=Severity.none, notes=message[:200])

        escalate = bool(parsed.get("escalate"))
        reason = parsed.get("escalate_reason")

        lower = message.lower()
        for keyword, sev in ALARM_KEYWORDS.items():
            if keyword in lower and sev == Severity.severe:
                escalate = True
                reason = reason or f"Regla de seguridad: {keyword}"
                state.severity = Severity.severe
                if keyword not in state.symptoms:
                    state.symptoms.append(keyword)
        return escalate, reason, state
