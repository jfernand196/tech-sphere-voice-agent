import asyncio

from app.agent.llm_mock import MockLLMClient
from app.agent.reply_guard import SPOKEN_ALERT_SENTENCE, SPOKEN_WATCH_PLAN


def test_demo_red_flag_turn_speaks_alert_without_reading_pdf_title() -> None:
    client = MockLLMClient(model_id="mock")
    parsed = asyncio.run(
        client.complete(
            patient_name="Ana Ángela Sánchez",
            procedure="colecistectomía",
            dia_postop=7,
            message=(
                "Hola tengo secreción purulenta Tengo un dolor 6 de 10 "
                "y tengo fiebre de 38 con 5"
            ),
            history=[],
            rag_context=[
                {
                    "doc_id": "cholecystitis",
                    "title": (
                        "[cholecystitis] Diagnóstico y tratamiento del paciente "
                        "con colecistitis aguda calculosa en el Hospital "
                        "Universitario Nacional de Colombia"
                    ),
                    "chunk_id": "c1",
                    "text": "Fiebre y secreción purulenta son signos de alarma.",
                }
            ],
        )
    )
    reply = parsed["reply"]
    assert parsed["escalate"] is True
    assert "secreción" in reply.lower()
    assert "fiebre" in reply.lower()
    assert SPOKEN_ALERT_SENTENCE in reply
    assert SPOKEN_WATCH_PLAN in reply
    assert "Hospital Universitario" not in reply
    assert "Según" not in reply
    assert "¿" not in reply
    assert "fiebre alta" in reply


def test_fever_with_reading_does_not_reask_thermometer() -> None:
    client = MockLLMClient(model_id="mock")
    parsed = asyncio.run(
        client.complete(
            patient_name="Manuel",
            procedure="colecistectomía",
            dia_postop=3,
            message="tengo fiebre 37,4 y un dolor de cinco de 10",
            history=[],
            rag_context=[
                {
                    "doc_id": "p",
                    "title": "Protocolo post-operatorio genérico",
                    "chunk_id": "c1",
                    "text": "Reposo, líquidos y seguimiento cercano.",
                }
            ],
        )
    )
    assert parsed["escalate"] is False
    assert "termómetro" not in parsed["reply"]
    assert "37" in parsed["reply"] or "fiebre leve" in parsed["reply"].lower()


def test_fever_followup_does_not_repeat_thermometer_question() -> None:
    client = MockLLMClient(model_id="mock")
    parsed = asyncio.run(
        client.complete(
            patient_name="Manuel",
            procedure="colecistectomía",
            dia_postop=3,
            message="como te dije ahora tengo fiebre de 37,4",
            history=[
                {
                    "role": "patient",
                    "content": "tengo fiebre 37,4 y un dolor de cinco de 10",
                }
            ],
            rag_context=[
                {
                    "doc_id": "p",
                    "title": "Protocolo post-operatorio genérico",
                    "chunk_id": "c1",
                    "text": "Reposo y líquidos.",
                }
            ],
        )
    )
    assert "termómetro" not in parsed["reply"]
    assert "Desde cuándo" not in parsed["reply"]


def test_fever_of_38_is_not_called_alta() -> None:
    client = MockLLMClient(model_id="mock")
    parsed = asyncio.run(
        client.complete(
            patient_name="Ana",
            procedure="colecistectomía",
            dia_postop=7,
            message="tengo secreción purulenta y fiebre de 38 grados",
            history=[],
            rag_context=[
                {
                    "doc_id": "p",
                    "title": "Protocolo post-operatorio genérico",
                    "chunk_id": "c1",
                    "text": "Reportar secreción purulenta.",
                }
            ],
        )
    )
    assert parsed["escalate"] is True
    assert "fiebre alta" not in parsed["reply"]
    assert "fiebre" in parsed["reply"]
