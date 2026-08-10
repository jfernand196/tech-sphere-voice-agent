import { useLocale } from "../i18n/LocaleContext";
import {
  summaryMetricsLegend,
  turnMetricsLegend,
  type MetricsHintItem,
} from "../metricsLegend";

export type { MetricsHintItem };

type Variant = "turn" | "summary";

type Props = {
  variant: Variant;
};

const VARIANT: Record<
  Variant,
  {
    className: string;
    titleKey: "call.metricsHintTitle" | "summary.metricsHintTitle";
    iconOnly: boolean;
    items: typeof turnMetricsLegend;
  }
> = {
  turn: {
    className: "metrics-hint--inline",
    titleKey: "call.metricsHintTitle",
    iconOnly: true,
    items: turnMetricsLegend,
  },
  summary: {
    className: "metrics-hint--summary",
    titleKey: "summary.metricsHintTitle",
    iconOnly: false,
    items: summaryMetricsLegend,
  },
};

/** Collapsible legend: bubble tip (`turn`) or hang-up card (`summary`). */
export default function MetricsHint({ variant }: Props) {
  const { t } = useLocale();
  const cfg = VARIANT[variant];
  const title = t(cfg.titleKey);
  const items = cfg.items(t);

  return (
    <details className={["metrics-hint", cfg.className].join(" ")}>
      <summary aria-label={title}>
        <span className="metrics-hint__icon" aria-hidden>
          i
        </span>
        {cfg.iconOnly ? null : <span>{title}</span>}
      </summary>
      {cfg.iconOnly ? <p className="metrics-hint__title">{title}</p> : null}
      <dl className="metrics-hint__list">
        {items.map((item) => (
          <div key={item.term}>
            <dt>{item.term}</dt>
            <dd>{item.definition}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
