import { useState } from "react";
import {
  dedupeTrimmedStrings,
  formatPairMs,
  hasMeaningfulCallMetrics,
} from "../callFormat";
import { severityText } from "../clinicalFormat";
import { useLocale } from "../i18n/LocaleContext";
import { displayDocTitle } from "../knowledgeFormat";
import type { CallSummary } from "../types";
import ChipRow from "./ChipRow";
import Disclosure from "./Disclosure";

type Props = {
  summary: CallSummary;
  onNewCall: () => void;
};

const SYMPTOM_CHIP_LIMIT = 6;

function SymptomChips({ items }: { items: string[] }) {
  const { t } = useLocale();
  const [expanded, setExpanded] = useState(false);
  const unique = dedupeTrimmedStrings(items);
  const hidden = Math.max(0, unique.length - SYMPTOM_CHIP_LIMIT);
  const visible =
    expanded || hidden === 0 ? unique : unique.slice(0, SYMPTOM_CHIP_LIMIT);

  return (
    <div className="symptom-chips">
      <ChipRow items={visible.map((s) => ({ key: s, label: s }))} />
      {hidden > 0 ? (
        <button
          type="button"
          className="symptom-chips__more"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded
            ? t("summary.showFewerSymptoms")
            : t("summary.showMoreSymptoms", { n: hidden })}
        </button>
      ) : null}
    </div>
  );
}

function ChallengeMetrics({ summary }: { summary: CallSummary }) {
  const { t } = useLocale();
  if (!hasMeaningfulCallMetrics(summary)) return null;

  return (
    <Disclosure
      className="disclosure--metrics"
      kicker={t("summary.metricsKicker")}
      title={t("summary.metricsTitle")}
    >
      <dl className="summary-grid summary-grid--metrics">
        <div>
          <dt>{t("summary.tokens")}</dt>
          <dd>
            {summary.tokens_in_total ?? 0} / {summary.tokens_out_total ?? 0}
          </dd>
        </div>
        <div>
          <dt>{t("summary.llmRag")}</dt>
          <dd>
            {t("summary.llmRagValue", {
              inv: summary.model_invocations_total ?? 0,
              rag: summary.rag_queries_total ?? 0,
            })}
          </dd>
        </div>
        <div className="summary-grid__wide">
          <dt>{t("summary.latency")}</dt>
          <dd>
            {summary.e2e_latency_p50_ms != null ? (
              <>
                {t("summary.latencyE2e", {
                  pair: formatPairMs(
                    summary.e2e_latency_p50_ms,
                    summary.e2e_latency_p95_ms,
                  ),
                })}{" "}
                ·{" "}
              </>
            ) : null}
            {t("summary.latencyApi", {
              pair: formatPairMs(
                summary.agent_latency_p50_ms,
                summary.agent_latency_p95_ms,
              ),
            })}
          </dd>
        </div>
        {summary.cost_usd_estimate != null ? (
          <div className="summary-grid__wide">
            <dt>{t("summary.cost")}</dt>
            <dd title={summary.cost_note ?? undefined}>
              ${summary.cost_usd_estimate.toFixed(4)} USD
            </dd>
          </div>
        ) : null}
      </dl>
    </Disclosure>
  );
}

function SourceChips({
  sources,
}: {
  sources: CallSummary["sources_used"];
}) {
  return (
    <ChipRow
      items={sources.map((s) => ({
        key: s.chunk_id,
        label: displayDocTitle(s.title, 42),
        title: s.title,
        className: "chip chip--source",
      }))}
    />
  );
}

export default function CallSummaryCard({ summary, onNewCall }: Props) {
  const { t } = useLocale();
  const [showRaw, setShowRaw] = useState(false);

  return (
    <section className="summary-card enter">
      <div className="summary-card__head">
        <div>
          <p className="eyebrow">{t("summary.eyebrow")}</p>
          <h3>{t("summary.title")}</h3>
        </div>
        <div className="summary-card__alert">
          <span
            className={`badge ${summary.escalate ? "badge--danger" : "badge--ok"}`}
          >
            {summary.escalate ? t("summary.alertYes") : t("summary.alertNo")}
          </span>
          {summary.escalate_reason ? (
            <p className="summary-reason">
              {t("summary.escalateReason", { reason: summary.escalate_reason })}
            </p>
          ) : null}
        </div>
      </div>

      <p className="summary-card__text">{summary.summary_text}</p>

      <dl className="summary-grid">
        <div>
          <dt>{t("summary.patient")}</dt>
          <dd>{summary.patient_name}</dd>
        </div>
        <div>
          <dt>{t("summary.procedure")}</dt>
          <dd>{summary.procedure}</dd>
        </div>
        <div>
          <dt>{t("summary.severity")}</dt>
          <dd>{severityText(summary.severity, t)}</dd>
        </div>
        <div>
          <dt>{t("summary.turns")}</dt>
          <dd>{summary.turn_count}</dd>
        </div>
        <div className="summary-grid__wide">
          <dt>{t("summary.symptoms")}</dt>
          <dd>
            {summary.symptoms.length ? (
              <SymptomChips items={summary.symptoms} />
            ) : (
              t("summary.noSymptoms")
            )}
          </dd>
        </div>
        <div className="summary-grid__wide">
          <dt>{t("summary.sources")}</dt>
          <dd>
            {summary.sources_used.length ? (
              <SourceChips sources={summary.sources_used} />
            ) : (
              t("summary.noSources")
            )}
          </dd>
        </div>
      </dl>

      <ChallengeMetrics summary={summary} />

      <div className="summary-actions">
        <button type="button" onClick={onNewCall}>
          {t("summary.newCall")}
        </button>
        <button
          type="button"
          className="secondary"
          onClick={() => setShowRaw((v) => !v)}
        >
          {showRaw ? t("summary.hideJson") : t("summary.showJson")}
        </button>
      </div>

      {showRaw ? (
        <pre className="raw-json">{JSON.stringify(summary, null, 2)}</pre>
      ) : null}
    </section>
  );
}
