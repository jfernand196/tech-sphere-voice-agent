import { severityChip } from "../clinicalFormat";
import { displayDocTitle } from "../knowledgeFormat";
import type { ChatItem } from "../types";

type Props = {
  message: ChatItem;
};

export default function ChatMessage({ message }: Props) {
  const isAgent = message.role === "agent";
  const severity = severityChip(message.patient_state?.severity);

  return (
    <article className={`bubble ${message.role}`}>
      <header className="bubble__meta">
        <strong>{isAgent ? "Agente" : "Paciente"}</strong>
        {severity ? (
          <span className={`sev-chip sev-chip--${message.patient_state?.severity}`}>
            {severity}
          </span>
        ) : null}
        {typeof message.latency_ms === "number" ? (
          <small>{message.latency_ms} ms</small>
        ) : null}
      </header>
      <p>{message.content}</p>
      {message.escalate ? (
        <div className="alert">Alerta humana — {message.escalate_reason || "revisar caso"}</div>
      ) : null}
      {message.sources && message.sources.length > 0 ? (
        <ul className="chip-row">
          {message.sources.map((s) => (
            <li
              key={s.chunk_id}
              className="chip chip--source"
              title={s.excerpt ? `${s.title}\n\n${s.excerpt}` : s.title}
            >
              {displayDocTitle(s.title, 42)}
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}
