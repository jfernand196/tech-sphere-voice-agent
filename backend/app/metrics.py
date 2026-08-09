"""Challenge metrics helpers (P50/P95, token usage, cost) — SRP outside CallService."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from app.schemas import CallMessage

# Groq list prices for Llama 3.3 70B (USD / 1M tokens). Free tier ≈ $0 at runtime.
GROQ_LLAMA33_70B_INPUT_PER_M = 0.59
GROQ_LLAMA33_70B_OUTPUT_PER_M = 0.79
COST_NOTE = (
    "Production list-price estimate for Groq Llama 3.3 70B "
    "($0.59/M in + $0.79/M out). Challenge free tier ≈ $0 at runtime."
)

Usage = Optional[Tuple[int, int]]


def percentile(values: Sequence[float], p: float) -> Optional[float]:
    """Linear-interpolation percentile; p in [0, 100]."""
    if not values:
        return None
    ordered = sorted(float(v) for v in values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (p / 100.0) * (len(ordered) - 1)
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def as_int_ms(value: Optional[float]) -> Optional[int]:
    if value is None:
        return None
    return int(round(value))


def estimate_cost_usd(
    tokens_in: int,
    tokens_out: int,
    *,
    input_per_m: float = GROQ_LLAMA33_70B_INPUT_PER_M,
    output_per_m: float = GROQ_LLAMA33_70B_OUTPUT_PER_M,
) -> float:
    return (tokens_in / 1_000_000.0) * input_per_m + (tokens_out / 1_000_000.0) * output_per_m


def usage_openai_compat(payload: Mapping[str, Any]) -> Usage:
    """OpenAI / Groq chat.completions `usage` block."""
    raw = payload.get("usage") or {}
    if not raw:
        return None
    return (
        int(raw.get("prompt_tokens") or 0),
        int(raw.get("completion_tokens") or 0),
    )


def usage_gemini(payload: Mapping[str, Any]) -> Usage:
    raw = payload.get("usageMetadata") or {}
    if not raw:
        return None
    return (
        int(raw.get("promptTokenCount") or 0),
        int(raw.get("candidatesTokenCount") or 0),
    )


def optional_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    return int(value)


@dataclass(frozen=True)
class CallMetricsRollup:
    patient_turns: int
    tokens_in_total: int
    tokens_out_total: int
    model_invocations_total: int
    rag_queries_total: int
    agent_latency_p50_ms: Optional[int]
    agent_latency_p95_ms: Optional[int]
    e2e_latency_p50_ms: Optional[int]
    e2e_latency_p95_ms: Optional[int]
    cost_usd_estimate: float
    cost_note: str


def rollup_call_metrics(
    messages: Sequence[CallMessage],
    e2e_latency_ms: Sequence[int] | None = None,
) -> CallMetricsRollup:
    """Aggregate per-turn metrics for CallSummary (DIP-friendly pure function)."""
    agent_latencies: list[float] = []
    tokens_in = 0
    tokens_out = 0
    model_invocations = 0
    rag_queries = 0
    patient_turns = 0

    for msg in messages:
        if msg.role == "patient":
            patient_turns += 1
        if msg.role == "agent" and msg.latency_ms is not None:
            agent_latencies.append(float(msg.latency_ms))
        if msg.tokens_in is not None:
            tokens_in += int(msg.tokens_in)
        if msg.tokens_out is not None:
            tokens_out += int(msg.tokens_out)
        if msg.model_invocations is not None:
            model_invocations += int(msg.model_invocations)
        if msg.rag_queries is not None:
            rag_queries += int(msg.rag_queries)

    e2e = [float(x) for x in (e2e_latency_ms or ()) if x is not None]
    return CallMetricsRollup(
        patient_turns=patient_turns,
        tokens_in_total=tokens_in,
        tokens_out_total=tokens_out,
        model_invocations_total=model_invocations,
        rag_queries_total=rag_queries,
        agent_latency_p50_ms=as_int_ms(percentile(agent_latencies, 50)),
        agent_latency_p95_ms=as_int_ms(percentile(agent_latencies, 95)),
        e2e_latency_p50_ms=as_int_ms(percentile(e2e, 50)),
        e2e_latency_p95_ms=as_int_ms(percentile(e2e, 95)),
        cost_usd_estimate=round(estimate_cost_usd(tokens_in, tokens_out), 6),
        cost_note=COST_NOTE,
    )


def attach_usage(parsed: Dict[str, Any], usage: Usage) -> Dict[str, Any]:
    """Inject provider usage into the LLM JSON payload (single place)."""
    if usage is None:
        return parsed
    parsed["tokens_in"] = int(usage[0])
    parsed["tokens_out"] = int(usage[1])
    return parsed
