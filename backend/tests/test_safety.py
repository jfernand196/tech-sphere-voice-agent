from app.agent.safety import assess_message, apply_safety_overrides
from app.schemas import PatientState, Severity


def test_assess_message_detects_severe_respiratory_alarm():
    result = assess_message("No puedo respirar bien")
    assert result.escalate is True
    assert result.severity == Severity.severe


def test_assess_message_fever_is_moderate_by_default():
    result = assess_message("Tengo fiebre de 38.2")
    assert result.escalate is False
    assert result.severity == Severity.moderate
    assert "fiebre" in result.symptoms


def test_assess_message_fever_plus_purulent_wound_escalates():
    result = assess_message(
        "Temperatura como de 38 grados. La herida la veo con secreción purulenta."
    )
    assert result.escalate is True
    assert result.severity == Severity.severe
    assert result.escalate_reason == "Fiebre + signos de infección en la herida"


def test_safety_override_forces_escalate_for_severe_keywords():
    state = PatientState(symptoms=[], severity=Severity.mild)
    escalate, reason, updated = apply_safety_overrides(
        "me duele el pecho mucho",
        escalate=False,
        escalate_reason=None,
        patient_state=state,
    )
    assert escalate is True
    assert reason
    assert updated.severity == Severity.severe


def test_assess_message_fever_plus_yellow_discharge_escalates():
    """Demo line: yellow wound fluid + fever is the fever+wound composite."""
    result = assess_message(
        "Me duele la herida y veo secreción amarilla; creo que tengo fiebre."
    )
    assert result.escalate is True
    assert result.severity == Severity.severe
    assert "fiebre+herida" in result.symptoms
    assert result.escalate_reason == "Fiebre + signos de infección en la herida"


def test_assess_message_fever_plus_yellow_liquid_escalates():
    result = assess_message("Tengo fiebre y sale líquido amarillo de la herida")
    assert result.escalate is True
    assert result.severity == Severity.severe
    assert "fiebre+herida" in result.symptoms


def test_assess_message_high_pain_plus_fever_escalates():
    result = assess_message("Dolor 9/10 y tengo fiebre")
    assert result.escalate is True
    assert result.severity == Severity.severe
    assert "dolor+fiebre" in result.symptoms
    assert result.escalate_reason == "Dolor alto + fiebre"


def test_assess_message_intense_pain_plus_fever_escalates():
    result = assess_message("Tengo dolor intenso y estoy afiebrado")
    assert result.escalate is True
    assert result.severity == Severity.severe
    assert "dolor+fiebre" in result.symptoms


def test_denied_pus_does_not_escalate():
    result = assess_message(
        "no no tiene mal olor y no está muy roja y tampoco está saliendo pus"
    )
    assert result.escalate is False
    assert result.severity != Severity.severe


def test_no_hay_pus_does_not_escalate():
    assert assess_message("no hay pus").escalate is False
    assert assess_message("sin pus en la herida").escalate is False


def test_affirmed_pus_still_escalates():
    result = assess_message("Tengo pus en la herida y fiebre de 38")
    assert result.escalate is True
    assert "pus" in result.symptoms


def test_uncertain_pus_still_escalates():
    """'no sé si' is not a denial; missing a real pus mention is worse than a false alarm."""
    result = assess_message("no sé si es pus")
    assert result.escalate is True


def test_denied_pus_does_not_block_probe_denial():
    from app.agent.safety import is_probe_denial

    assert is_probe_denial(
        "no no tiene mal olor y no está muy roja y tampoco está saliendo pus"
    )


def test_fever_plus_denied_pus_does_not_composite():
    result = assess_message("tengo fiebre de 38 y tampoco está saliendo pus")
    assert result.escalate is False
    assert "fiebre+herida" not in result.symptoms


def test_safety_override_does_not_force_on_denied_pus():
    state = PatientState(symptoms=[], severity=Severity.mild)
    escalate, reason, updated = apply_safety_overrides(
        "tampoco está saliendo pus",
        escalate=False,
        escalate_reason=None,
        patient_state=state,
    )
    assert escalate is False
    assert updated.severity != Severity.severe
    _ = reason


def test_safety_override_forces_composite_when_model_said_no():
    state = PatientState(symptoms=["dolor"], severity=Severity.mild)
    escalate, reason, updated = apply_safety_overrides(
        "Me duele la herida y veo secreción amarilla; creo que tengo fiebre.",
        escalate=False,
        escalate_reason=None,
        patient_state=state,
    )
    assert escalate is True
    assert reason == "Fiebre + signos de infección en la herida"
    assert updated.severity == Severity.severe


def test_safety_override_forces_escalate_for_doctor_request():
    state = PatientState(symptoms=[], severity=Severity.mild)
    escalate, reason, updated = apply_safety_overrides(
        "quiero un doctor ahora",
        escalate=False,
        escalate_reason=None,
        patient_state=state,
    )
    assert escalate is True
    assert reason
    assert updated.severity == Severity.moderate


def test_safety_override_drops_llm_escalate_on_clean_denial() -> None:
    state = PatientState(symptoms=["fiebre"], severity=Severity.moderate)
    escalate, reason, _ = apply_safety_overrides(
        "Por el momento no he notado eso",
        escalate=True,
        escalate_reason="Febrícula y dolor moderado",
        patient_state=state,
        history=[
            {
                "role": "patient",
                "content": "Hola tengo fiebre 37,4 y tengo un dolor 5 de 10",
            }
        ],
    )
    assert escalate is False
    assert reason is None


def test_safety_override_keeps_escalate_if_history_had_wound_alarm() -> None:
    state = PatientState(symptoms=["fiebre"], severity=Severity.moderate)
    escalate, reason, _ = apply_safety_overrides(
        "Por el momento no he notado eso",
        escalate=True,
        escalate_reason="sigue en observación",
        patient_state=state,
        history=[
            {
                "role": "patient",
                "content": "Tengo fiebre y secreción purulenta en la herida",
            }
        ],
    )
    assert escalate is True
    assert reason


def test_humanize_symptoms_drops_detector_tokens() -> None:
    from app.agent.safety import humanize_symptoms

    out = humanize_symptoms(
        ["secreción purulenta", "fiebre", "38", "fiebre+herida", "dolor"]
    )
    assert out == ["secreción purulenta", "fiebre", "dolor"]
    assert "38" not in out
    assert "fiebre+herida" not in out


def test_fever_word_only_says_alta_from_38_5() -> None:
    from app.agent.safety import fever_word, wants_wound_followup

    assert fever_word("fiebre de 38 grados") == "fiebre"
    assert fever_word("fiebre de 38,5") == "fiebre alta"
    assert fever_word("38 con 5") == "fiebre alta"
    assert wants_wound_followup("secreción purulenta y fiebre") is True
    assert wants_wound_followup("protocolo ZETA-42") is False
