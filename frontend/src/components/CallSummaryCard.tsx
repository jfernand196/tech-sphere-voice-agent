import { useState } from "react";
import { formatPairMs, hasCallMetrics } from "../callFormat";
import { severityText } from "../clinicalFormat";
import { displayDocTitle } from "../knowledgeFormat";
import type { CallSummary } from "../types";

type Props = {
  summary: CallSummary;
  onNewCall: () => void;
};

function ChipList({ items }: { items: string[] }) {
  return (
    <ul className="chip-row">
      {items.map((s) => (
        <li key={s} className="chip">
          {s}
        </li>
      ))}
    </ul>
  );
}

function MetricsBlock({ summary }: { summary: CallSummary }) {
  if (!hasCallMetrics(summary)) return null;
  return (
    <>
      <div>
        <dt>Tokens (in/out)</dt>
        <dd>
          {summary.tokens_in_total ?? 0} / {summary.tokens_out_total ?? 0}
        </dd>
      </div>
      <div>
        <dt>LLM / RAG</dt>
        <dd>
          {summary.model_invocations_total ?? 0} inv · {summary.rag_queries_total ?? 0} RAG
        </dd>
      </div>
      <div className="summary-grid__wide">
        <dt>Latencia P50 / P95</dt>
        <dd>
          {summary.e2e_latency_p50_ms != null ? (
            <>e2e voz {formatPairMs(summary.e2e_latency_p50_ms, summary.e2e_latency_p95_ms)} · </>
          ) : null}
          api {formatPairMs(summary.agent_latency_p50_ms, summary.agent_latency_p95_ms)}
        </dd>
      </div>
      {summary.cost_usd_estimate != null ? (
        <div className="summary-grid__wide">
          <dt>Costo est. (prod)</dt>
          <dd title={summary.cost_note ?? undefined}>
            ${summary.cost_usd_estimate.toFixed(4)} USD
          </dd>
        </div>
      ) : null}
    </>
  );
}

export default function CallSummaryCard({ summary, onNewCall }: Props) {
  const [showRaw, setShowRaw] = useState(false);

  return (
    <section className="summary-card enter">
      <div className="summary-card__head">
        <div>
          <p className="eyebrow">Llamada finalizada</p>
          <h3>Resumen clínico</h3>
        </div>
        <span className={`badge ${summary.escalate ? "badge--danger" : "badge--ok"}`}>
          {summary.escalate ? "Alertar humano" : "Sin alerta"}
        </span>
      </div>

      <p className="summary-card__text">{summary.summary_text}</p>

      <dl className="summary-grid">
        <div>
          <dt>Paciente</dt>
          <dd>{summary.patient_name}</dd>
        </div>
        <div>
          <dt>Procedimiento</dt>
          <dd>{summary.procedure}</dd>
        </div>
        <div>
          <dt>Severidad</dt>
          <dd>{severityText(summary.severity)}</dd>
        </div>
        <div>
          <dt>Turnos</dt>
          <dd>{summary.turn_count}</dd>
        </div>
        <MetricsBlock summary={summary} />
        <div className="summary-grid__wide">
          <dt>Síntomas</dt>
          <dd>
            {summary.symptoms.length ? (
              <ChipList items={summary.symptoms} />
            ) : (
              "Ninguno reportado"
            )}
          </dd>
        </div>
        <div className="summary-grid__wide">
          <dt>Fuentes usadas</dt>
          <dd>
            {summary.sources_used.length ? (
              <ul className="chip-row">
                {summary.sources_used.map((s) => (
                  <li key={s.chunk_id} className="chip chip--source" title={s.title}>
                    {displayDocTitle(s.title, 42)}
                  </li>
                ))}
              </ul>
            ) : (
              "Sin citas"
            )}
          </dd>
        </div>
      </dl>

      {summary.escalate_reason ? (
        <p className="summary-reason">Motivo de alerta: {summary.escalate_reason}</p>
      ) : null}

      <div className="summary-actions">
        <button type="button" onClick={onNewCall}>
          Nueva llamada
        </button>
        <button
          type="button"
          className="secondary"
          onClick={() => setShowRaw((v) => !v)}
        >
          {showRaw ? "Ocultar JSON" : "Ver JSON técnico"}
        </button>
      </div>

      {showRaw ? <pre className="raw-json">{JSON.stringify(summary, null, 2)}</pre> : null}
    </section>
  );
}
