import { useLocale } from "../i18n/LocaleContext";

type Props = {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onListen: () => void;
  busy: boolean;
  listening: boolean;
};

/** Sticky text + speak controls for the live call phase. */
export default function CallComposer({
  input,
  onInputChange,
  onSend,
  onListen,
  busy,
  listening,
}: Props) {
  const { t } = useLocale();
  const locked = busy || listening;

  return (
    <div className={`composer${listening ? " composer--listening" : ""}`}>
      <input
        value={input}
        onChange={(e) => onInputChange(e.target.value)}
        placeholder={
          listening ? t("call.listeningPlaceholder") : t("call.placeholder")
        }
        onKeyDown={(e) => {
          if (e.key === "Enter") onSend();
        }}
        disabled={locked}
      />
      <button
        type="button"
        className="secondary"
        onClick={onSend}
        disabled={locked || !input.trim()}
      >
        {t("call.send")}
      </button>
      <button
        type="button"
        className={listening ? "btn-listen" : undefined}
        onClick={onListen}
        disabled={locked}
        aria-pressed={listening}
      >
        {listening ? t("call.listening") : t("call.speak")}
      </button>
    </div>
  );
}
