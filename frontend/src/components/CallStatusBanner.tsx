import { useLocale } from "../i18n/LocaleContext";

type Variant = "listening" | "thinking";

type Props = {
  variant: Variant;
};

/** Shared call-status strip (mic open vs agent turn in flight). */
export default function CallStatusBanner({ variant }: Props) {
  const { t } = useLocale();
  const thinking = variant === "thinking";
  return (
    <div
      className={`call-status${thinking ? " call-status--thinking" : ""}`}
      role="status"
      aria-live={thinking ? "polite" : "assertive"}
    >
      <span
        className={`call-status__pulse${thinking ? " call-status__pulse--think" : ""}`}
        aria-hidden
      />
      <div>
        <strong>{t(thinking ? "call.thinking" : "call.listening")}</strong>
        <p>{t(thinking ? "call.thinkingHint" : "call.listeningHint")}</p>
      </div>
    </div>
  );
}
