import { hasTurnMetrics, turnMetricBits } from "../callFormat";
import { severityChip } from "../clinicalFormat";
import { useLocale } from "../i18n/LocaleContext";
import { truncateEllipsis } from "../textFormat";
import type { ChatItem } from "../types";
import MetricsHint from "./MetricsHint";
import SourceChipRow from "./SourceChipRow";

type Props = {
  message: ChatItem;
  /** Only the latest metered agent bubble shows the legend control. */
  showMetricsHint?: boolean;
};

const ALERT_REASON_MAX = 90;

function TurnMetrics({
  message,
  showHint,
}: {
  message: ChatItem;
  showHint: boolean;
}) {
  const { t } = useLocale();
  const bits = turnMetricBits(message, {
    e2e: t("chat.e2eTitle"),
    api: t("chat.apiTitle"),
    tok: t("chat.tokTitle"),
  });
  if (bits.length === 0) return null;

  return (
    <div className="bubble__metrics-block">
      <div className="bubble__metrics-row">
        <p className="bubble__metrics" aria-label={t("chat.metricsAria")}>
          {bits.map((b, i) => (
            <span key={b.text} title={b.title}>
              {i > 0 ? " · " : null}
              {b.text}
            </span>
          ))}
        </p>
        {showHint ? <MetricsHint variant="turn" /> : null}
      </div>
    </div>
  );
}

function EscalateAlert({ reason }: { reason: string }) {
  const { t } = useLocale();
  return (
    <div className="alert" title={reason}>
      <span className="alert__label">{t("chat.escalateLabel")}</span>
      <span className="alert__reason">
        {truncateEllipsis(reason, ALERT_REASON_MAX)}
      </span>
    </div>
  );
}

export default function ChatMessage({
  message,
  showMetricsHint = false,
}: Props) {
  const { t } = useLocale();
  const isAgent = message.role === "agent";
  const severity = severityChip(message.patient_state?.severity, t);

  return (
    <article className={`bubble ${message.role}`}>
      <header className="bubble__meta">
        <strong>{isAgent ? t("chat.agent") : t("chat.patient")}</strong>
        {severity ? (
          <span
            className={`sev-chip sev-chip--${message.patient_state?.severity}`}
          >
            {severity}
          </span>
        ) : null}
      </header>
      <p>{message.content}</p>
      {isAgent && hasTurnMetrics(message) ? (
        <TurnMetrics message={message} showHint={showMetricsHint} />
      ) : null}
      {message.escalate ? (
        <EscalateAlert
          reason={message.escalate_reason || t("chat.escalateFallback")}
        />
      ) : null}
      {message.sources?.length ? (
        <SourceChipRow sources={message.sources} withExcerpt />
      ) : null}
    </article>
  );
}
