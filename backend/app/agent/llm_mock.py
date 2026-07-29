"""Mock LLM adapter: offline-friendly clinical replies grounded in RAG."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from app.agent.parsing import clean_excerpt
from app.agent.safety import assess_message, severity_rank
from app.schemas import Severity


class MockLLMClient:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    async def complete(
        self,
        *,
        patient_name: str,
        procedure: str,
        message: str,
        history: List[Dict[str, str]],
        rag_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        _ = (patient_name, procedure, history)
        assessment = assess_message(message)
        lower = message.lower()
        escalate = assessment.escalate
        reason = assessment.escalate_reason
        severity = assessment.severity if assessment.symptoms else Severity.mild
        symptoms = list(assessment.symptoms)

        sources = [
            {
                "doc_id": c["doc_id"],
                "title": c["title"],
                "chunk_id": c["chunk_id"],
                "excerpt": clean_excerpt(c["text"]),
            }
            for c in rag_context[:2]
        ]

        if rag_context:
            reply = _compose_clinical_reply(
                message=lower,
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

        if symptoms and severity_rank(severity) < severity_rank(Severity.mild):
            severity = Severity.mild

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


def _compose_clinical_reply(
    *,
    message: str,
    escalate: bool,
    doc_title: str,
    context_text: str,
) -> str:
    ctx = context_text.lower()

    if "respir" in message or "pecho" in message:
        return (
            f"Entiendo, eso suena urgente. Según {doc_title}, la dificultad para respirar "
            "o el dolor en el pecho son signos de alarma. Quédate en un lugar seguro; "
            "voy a alertar a personal capacitado ahora mismo."
        )

    if "sangr" in message:
        if escalate:
            return (
                f"Gracias por avisarme. En {doc_title} el sangrado abundante se considera "
                "signo de alarma. ¿La sangre empapa apósitos con rapidez o solo hay un poco "
                "en la gasa? Mientras tanto marco revisión humana."
            )
        return (
            f"Anoto el sangrado. Según {doc_title}, necesitamos saber si es abundante. "
            "¿Cuántas gasas has cambiado en la última hora?"
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
