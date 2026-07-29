import type { ChatItem } from "../hooks/useCallSession";

type Props = {
  message: ChatItem;
};

export default function ChatMessage({ message }: Props) {
  return (
    <article className={`bubble ${message.role}`}>
      <strong>{message.role === "agent" ? "Agente" : "Paciente"}</strong>
      <p>{message.content}</p>
      {message.escalate ? (
        <div className="alert">
          ALERTA HUMANO — {message.escalate_reason || "revisar caso"}
        </div>
      ) : null}
      {message.sources && message.sources.length > 0 ? (
        <ul className="sources">
          {message.sources.map((s) => (
            <li key={s.chunk_id}>
              <code>{s.title}</code> · {s.chunk_id}
            </li>
          ))}
        </ul>
      ) : null}
      {typeof message.latency_ms === "number" ? (
        <small>{message.latency_ms} ms</small>
      ) : null}
    </article>
  );
}
