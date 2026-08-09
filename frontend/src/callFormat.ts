import type { AgentTurnResponse, CallSummary, ChatItem } from "./types";

/** Map API turn (+ optional E2E ms) → chat bubble — single mapping site. */
export function agentChatItemFromTurn(
  turn: AgentTurnResponse,
  e2eMs?: number,
): ChatItem {
  return {
    role: "agent",
    content: turn.reply,
    sources: turn.sources,
    escalate: turn.escalate,
    escalate_reason: turn.escalate_reason,
    patient_state: turn.patient_state,
    latency_ms: turn.latency_ms,
    e2e_latency_ms: e2eMs,
    tokens_in: turn.tokens_in,
    tokens_out: turn.tokens_out,
  };
}

export function formatPairMs(p50?: number | null, p95?: number | null): string {
  return `${p50 ?? "—"}/${p95 ?? "—"} ms`;
}

export function hasCallMetrics(summary: CallSummary): boolean {
  return (
    summary.tokens_in_total != null ||
    summary.model_invocations_total != null ||
    summary.agent_latency_p50_ms != null ||
    summary.e2e_latency_p50_ms != null ||
    summary.cost_usd_estimate != null
  );
}
