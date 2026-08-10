import type { MessageKey } from "./i18n";

export type MetricsHintItem = {
  term: string;
  definition: string;
};

type TFn = (key: MessageKey) => string;

/** Shared e2e/api definitions (DRY across live bubble + hang-up summary). */
function latencyItems(t: TFn): MetricsHintItem[] {
  return [
    { term: "e2e", definition: t("call.metricsHintE2e") },
    { term: "api", definition: t("call.metricsHintApi") },
  ];
}

export function turnMetricsLegend(t: TFn): MetricsHintItem[] {
  return [
    ...latencyItems(t),
    { term: "tok", definition: t("call.metricsHintTok") },
  ];
}

export function summaryMetricsLegend(t: TFn): MetricsHintItem[] {
  return [
    ...latencyItems(t),
    { term: "tok", definition: t("summary.metricsHintTok") },
    { term: "P50/P95", definition: t("summary.metricsHintPercentiles") },
    { term: "LLM/RAG", definition: t("summary.metricsHintLlmRag") },
    {
      term: t("summary.metricsTermCost"),
      definition: t("summary.metricsHintCost"),
    },
  ];
}
