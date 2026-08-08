import type { ChatItem } from "../hooks/useCallSession";

type Props = {
  message: ChatItem;
};

export default function ChatMessage({ message }: Props) {
  const isAgent = message.role === "agent";

  return (
    <article className={`bubble ${message.role}`}>
      <header className="bubble__meta">
        <strong>{isAgent ? "Agente" : "Paciente"}</strong>
        {message.patient_state?.severity && message.patient_state.severity !== "none" ? (
          <small>sev: {message.patient_state.severity}</small>
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
            <li key={s.chunk_id} className="chip chip--source" title={s.excerpt ?? s.chunk_id}>
              {s.title}
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}
