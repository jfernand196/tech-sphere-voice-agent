"""Prompt contract: live knowledge must not be re-sourced from chat history."""

from app.agent.prompts import SYSTEM_PROMPT, build_user_prompt


def test_system_prompt_forbids_history_as_protocol_source():
    lower = SYSTEM_PROMPT.lower()
    assert "conocimiento vivo" in lower
    assert "no uses el historial como fuente" in lower
    assert "ya no aparece" in lower or "documento eliminado" in lower


def test_system_prompt_asks_before_deciding_on_ambiguity():
    assert "ambigüedad" in SYSTEM_PROMPT.lower()
    assert "indaga" in SYSTEM_PROMPT.lower()


def test_system_prompt_has_soft_agenda_and_long_instruction_policy():
    lower = SYSTEM_PROMPT.lower()
    assert "agenda suave" in lower
    assert "una indicación" in lower or "una indicación concreta" in lower
    assert "fuera de guion" in lower
    assert "asustado" in lower or "hostil" in lower


def test_user_prompt_labels_history_vs_live_rag():
    text = build_user_prompt(
        patient_name="Ana",
        procedure="colecistectomia",
        dia_postop=3,
        message="¿qué decía el protocolo ZETA?",
        history=[
            {"role": "agent", "content": "Según ZETA camina 5 minutos."},
            {"role": "user", "content": "ok"},
        ],
        rag_context=[],
    )
    assert "NO es fuente de protocolos" in text
    assert "única fuente clínica" in text
    assert "no la tomes del historial" in text
    assert "(sin material de referencia)" in text
    assert "Según ZETA camina 5 minutos." in text
