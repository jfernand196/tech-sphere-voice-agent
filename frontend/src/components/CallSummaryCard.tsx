import { useState } from "react";
import { severityText } from "../clinicalFormat";
import { displayDocTitle } from "../knowledgeFormat";
import type { CallSummary } from "../types";

type Props = {
  summary: CallSummary;
  onNewCall: () => void;
};

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
        <div className="summary-grid__wide">
          <dt>Síntomas</dt>
          <dd>
            {summary.symptoms.length ? (
              <ul className="chip-row">
                {summary.symptoms.map((s) => (
                  <li key={s} className="chip">
                    {s}
                  </li>
                ))}
              </ul>
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
