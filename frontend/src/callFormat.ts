import type { AgentTurnResponse, CallSummary, ChatItem } from "./types";

export type TurnMetricBit = { title: string; text: string };

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

type TurnMetricsSource = Pick<
  ChatItem,
  "e2e_latency_ms" | "latency_ms" | "tokens_in" | "tokens_out"
>;

export function hasTurnMetrics(message: TurnMetricsSource): boolean {
  return (
    typeof message.e2e_latency_ms === "number" ||
    typeof message.latency_ms === "number" ||
    (typeof message.tokens_in === "number" &&
      typeof message.tokens_out === "number")
  );
}

/** Pure challenge turn metrics for bubble footers (no React). */
export function turnMetricBits(
  message: TurnMetricsSource,
  labels: { e2e: string; api: string; tok: string },
): TurnMetricBit[] {
  const bits: TurnMetricBit[] = [];
  if (typeof message.e2e_latency_ms === "number") {
    bits.push({ title: labels.e2e, text: `e2e ${message.e2e_latency_ms}` });
  }
  if (typeof message.latency_ms === "number") {
    bits.push({ title: labels.api, text: `api ${message.latency_ms}` });
  }
  if (
    typeof message.tokens_in === "number" &&
    typeof message.tokens_out === "number"
  ) {
    bits.push({
      title: labels.tok,
      text: `tok ${message.tokens_in}/${message.tokens_out}`,
    });
  }
  return bits;
}

/** Index of the latest agent bubble that carries challenge turn metrics. */
export function lastTurnMetricsIndex(messages: ChatItem[]): number {
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const m = messages[i];
    if (m?.role === "agent" && hasTurnMetrics(m)) return i;
  }
  return -1;
}

/** Trim + case-insensitive dedupe; keeps first spelling for display. */
export function dedupeTrimmedStrings(
  items: string[],
  locale = "es",
): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of items) {
    const trimmed = raw.trim();
    const key = trimmed.toLocaleLowerCase(locale);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    out.push(trimmed);
  }
  return out;
}

/** True when there is something useful to show (not a wall of zeros). */
export function hasMeaningfulCallMetrics(summary: CallSummary): boolean {
  return (
    (summary.tokens_in_total ?? 0) > 0 ||
    (summary.tokens_out_total ?? 0) > 0 ||
    (summary.model_invocations_total ?? 0) > 0 ||
    (summary.rag_queries_total ?? 0) > 0 ||
    (summary.agent_latency_p50_ms ?? 0) > 0 ||
    (summary.e2e_latency_p50_ms ?? 0) > 0 ||
    (summary.cost_usd_estimate ?? 0) > 0
  );
}
