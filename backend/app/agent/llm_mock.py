"""Mock LLM adapter: offline-friendly clinical replies grounded in RAG."""

from __future__ import annotations

from typing import Any, Dict, List

from app.agent.parsing import clean_excerpt
from app.agent.reply_guard import ensure_spoken_alert
from app.agent.safety import (
    assess_message,
    fever_word,
    has_bleeding_signal,
    has_fever_signal,
    has_respiratory_signal,
    has_stated_temperature,
    has_wound_mention,
    patient_conversation_text,
    severity_rank,
)
from app.schemas import Severity


class MockLLMClient:
    def __init__(self, model_id: str) -> None:
        self.model_id = model_id

    async def complete(
        self,
        *,
        patient_name: str,
        procedure: str,
        dia_postop: int,
        message: str,
        history: List[Dict[str, str]],
        rag_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        _ = (patient_name, procedure, dia_postop)
        assessment = assess_message(message)
        lower = message.lower()
        spoken_so_far = patient_conversation_text(message, history).lower()
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
                spoken_so_far=spoken_so_far,
                escalate=escalate,
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

        reply = ensure_spoken_alert(reply, escalate)

        if symptoms and severity_rank(severity) < severity_rank(Severity.mild):
            severity = Severity.mild

        # Rough local estimate so mock paths still exercise metrics fields.
        tokens_in = max(1, (len(message) + sum(len(c.get("text", "")) for c in rag_context)) // 4)
        tokens_out = max(1, len(reply) // 4)
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
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "model_id": self.model_id,
        }


def _compose_escalate_reply(message: str) -> str:
    """Voice close for alarm turns: acknowledge the picture, no extra questions."""
    wound = has_wound_mention(message)
    fever = has_fever_signal(message)
    if wound and fever:
        return (
            f"Te escucho: secreción en la herida junto con {fever_word(message)} "
            "son signos de alarma."
        )
    if wound:
        return "La secreción de la herida que describes es un signo de alarma."
    if has_respiratory_signal(message):
        return (
            "Eso suena urgente: la falta de aire o el dolor en el pecho "
            "son signos de alarma."
        )
    if has_bleeding_signal(message):
        return "Anoto el sangrado; si empapa apósitos es un signo de alarma."
    if fever:
        return f"Escucho la {fever_word(message)}; eso es un signo de alarma."
    if "dolor" in message:
        return "Ese dolor tan fuerte es un signo de alarma."
    return "Por lo que me cuentas, hay signos de alarma."


def _compose_clinical_reply(
    *,
    message: str,
    spoken_so_far: str,
    escalate: bool,
    context_text: str,
) -> str:
    if escalate:
        return _compose_escalate_reply(message)

    ctx = context_text.lower()
    picture = spoken_so_far or message

    if has_bleeding_signal(message):
        return (
            "Anoto el sangrado. Necesito saber si es abundante: "
            "¿cuántas gasas has cambiado en la última hora?"
        )

    if has_fever_signal(message) or has_fever_signal(picture):
        guidance = (
            "hidratación, reposo relativo y reevaluación en la siguiente hora"
            if "hidratación" in ctx or "hidratacion" in ctx
            else "reposo, líquidos y seguimiento cercano"
        )
        if has_stated_temperature(picture):
            return (
                f"Queda anotada la {fever_word(picture)} que me diste. "
                f"Con fiebre leve el protocolo sugiere {guidance}. "
                "Sigue líquidos y el analgésico indicado, y avísame si sube de 38.5, "
                "sale pus de la herida o te falta el aire."
            )
        return (
            f"Gracias por contármelo. Con fiebre leve el protocolo sugiere {guidance}. "
            "¿Desde cuándo la tienes y qué temperatura marcó el termómetro?"
        )

    if has_wound_mention(message):
        return (
            "Entiendo lo de la herida. El enrojecimiento leve puede ser esperado, "
            "pero pus, mal olor o puntos abiertos sí preocupan. "
            "¿Ves mal olor o se abrió algún punto?"
        )

    if "dolor" in message:
        return (
            "Lamento que estés con dolor. Cumple el analgésico indicado "
            "y avísame si no cede. Del 1 al 10, ¿qué tan fuerte es ahora?"
        )

    if "vómito" in message or "vomito" in message:
        return (
            "Anoto el vómito. Si es persistente e impide tomar líquidos, hay que alertar. "
            "¿Has podido retener agua o suero en las últimas horas?"
        )

    return (
        "Gracias, te escucho. Cuéntame el síntoma principal, desde cuándo lo tienes "
        "y qué tan intenso es del 1 al 10."
    )
