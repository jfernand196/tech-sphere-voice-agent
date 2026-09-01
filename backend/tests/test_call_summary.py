from pathlib import Path

from app.calls.service import CallService
from app.schemas import (
    AgentTurnResponse,
    PatientState,
    Severity,
    SourceCitation,
    StartCallRequest,
)


def test_hangup_summary_uses_readable_symptoms(tmp_path: Path) -> None:
    svc = CallService(tmp_path / "calls.json")
    record = svc.start(
        StartCallRequest(
            patient_name="Ana Ángela Sánchez",
            procedure="colecistectomía",
            dia_postop=7,
        ),
        greeting="Hola Ana",
    )
    svc.append_user(record.call_id, "secreción purulenta y fiebre de 38")
    svc.append_agent(
        record.call_id,
        AgentTurnResponse(
            reply="Voy a marcar una alerta para que un humano revise tu caso.",
            sources=[
                SourceCitation(
                    doc_id="d1",
                    title="PLAN DE CUIDADO COLECISTECTOMIA",
                    chunk_id="c1",
                    excerpt="alarma",
                )
            ],
            patient_state=PatientState(
                symptoms=["secreción purulenta", "fiebre", "38", "fiebre+herida", "dolor"],
                severity=Severity.severe,
            ),
            escalate=True,
            escalate_reason="fiebre y secreción purulenta",
        ),
    )
    ended = svc.end(record.call_id)
    assert ended.summary is not None
    assert ended.summary.symptoms == ["secreción purulenta", "fiebre", "dolor"]
    assert "38" not in ended.summary.symptoms
    assert "fiebre+herida" not in ended.summary.symptoms
    assert ended.summary.escalate is True
    assert "severa" in ended.summary.summary_text
    assert "severe" not in ended.summary.summary_text
