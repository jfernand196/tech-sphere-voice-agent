import { severityChip } from "../clinicalFormat";
import { displayDocTitle } from "../knowledgeFormat";
import type { ChatItem } from "../types";

type Props = {
  message: ChatItem;
};

function MetaBits({ message }: { message: ChatItem }) {
  const bits: { title: string; text: string }[] = [];
  if (typeof message.e2e_latency_ms === "number") {
    bits.push({
      title: "Voz→voz (fin habla → audio agente)",
      text: `e2e ${message.e2e_latency_ms} ms`,
    });
  }
  if (typeof message.latency_ms === "number") {
    bits.push({ title: "Solo backend (RAG+LLM)", text: `api ${message.latency_ms} ms` });
  }
  if (typeof message.tokens_in === "number" && typeof message.tokens_out === "number") {
    bits.push({
      title: "Tokens in / out",
      text: `tok ${message.tokens_in}/${message.tokens_out}`,
    });
  }
  return (
    <>
      {bits.map((b) => (
        <small key={b.text} title={b.title}>
          {b.text}
        </small>
      ))}
    </>
  );
}

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
        {isAgent ? <MetaBits message={message} /> : null}
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
