from app.metrics import (
    estimate_cost_usd,
    percentile,
    rollup_call_metrics,
    usage_gemini,
    usage_openai_compat,
)
from app.schemas import CallMessage


def test_percentile_p50_p95() -> None:
    values = [1200, 1300, 1400, 1500, 1500, 1600, 1800, 2000, 2200, 4000]
    assert percentile(values, 50) == 1550.0
    assert abs((percentile(values, 95) or 0) - 3190.0) < 0.01


def test_estimate_cost_positive() -> None:
    cost = estimate_cost_usd(100_000, 20_000)
    assert 0 < cost < 1.0


def test_usage_parsers() -> None:
    assert usage_openai_compat({"usage": {"prompt_tokens": 10, "completion_tokens": 4}}) == (
        10,
        4,
    )
    assert usage_openai_compat({}) is None
    assert usage_gemini({"usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 2}}) == (
        3,
        2,
    )


def test_rollup_call_metrics() -> None:
    messages = [
        CallMessage(role="agent", content="hola"),
        CallMessage(role="patient", content="dolor"),
        CallMessage(
            role="agent",
            content="ok",
            latency_ms=1000,
            tokens_in=100,
            tokens_out=40,
            model_invocations=1,
            rag_queries=1,
        ),
        CallMessage(role="patient", content="fiebre"),
        CallMessage(
            role="agent",
            content="alerta",
            latency_ms=2000,
            tokens_in=120,
            tokens_out=50,
            model_invocations=1,
            rag_queries=1,
        ),
    ]
    rollup = rollup_call_metrics(messages, e2e_latency_ms=[3000, 4000])
    assert rollup.patient_turns == 2
    assert rollup.tokens_in_total == 220
    assert rollup.tokens_out_total == 90
    assert rollup.model_invocations_total == 2
    assert rollup.rag_queries_total == 2
    assert rollup.agent_latency_p50_ms == 1500
    assert rollup.e2e_latency_p50_ms == 3500
