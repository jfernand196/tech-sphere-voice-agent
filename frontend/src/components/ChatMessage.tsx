import { severityChip } from "../clinicalFormat";
import { useLocale } from "../i18n/LocaleContext";
import { displayDocTitle } from "../knowledgeFormat";
import type { ChatItem } from "../types";
import ChipRow from "./ChipRow";

type Props = {
  message: ChatItem;
};

function MetaBits({ message }: { message: ChatItem }) {
  const { t } = useLocale();
  const bits: { title: string; text: string }[] = [];
  if (typeof message.e2e_latency_ms === "number") {
    bits.push({
      title: t("chat.e2eTitle"),
      text: `e2e ${message.e2e_latency_ms} ms`,
    });
  }
  if (typeof message.latency_ms === "number") {
    bits.push({ title: t("chat.apiTitle"), text: `api ${message.latency_ms} ms` });
  }
  if (typeof message.tokens_in === "number" && typeof message.tokens_out === "number") {
    bits.push({
      title: t("chat.tokTitle"),
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
  const { t } = useLocale();
  const isAgent = message.role === "agent";
  const severity = severityChip(message.patient_state?.severity, t);

  return (
    <article className={`bubble ${message.role}`}>
      <header className="bubble__meta">
        <strong>{isAgent ? t("chat.agent") : t("chat.patient")}</strong>
        {severity ? (
          <span className={`sev-chip sev-chip--${message.patient_state?.severity}`}>
            {severity}
          </span>
        ) : null}
        {isAgent ? <MetaBits message={message} /> : null}
      </header>
      <p>{message.content}</p>
      {message.escalate ? (
        <div className="alert">
          {t("chat.escalate", {
            reason: message.escalate_reason || t("chat.escalateFallback"),
          })}
        </div>
      ) : null}
      {message.sources && message.sources.length > 0 ? (
        <ChipRow
          items={message.sources.map((s) => ({
            key: s.chunk_id,
            label: displayDocTitle(s.title, 42),
            title: s.excerpt ? `${s.title}\n\n${s.excerpt}` : s.title,
            className: "chip chip--source",
          }))}
        />
      ) : null}
    </article>
  );
}
