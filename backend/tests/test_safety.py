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
