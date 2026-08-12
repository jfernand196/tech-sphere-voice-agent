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
