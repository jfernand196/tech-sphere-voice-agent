import { useLocale } from "../i18n/LocaleContext";
import type { VoiceOption } from "../speech";

type Props = {
  voiceOut: boolean;
  onVoiceOutChange: (value: boolean) => void;
  voices: VoiceOption[];
  voiceName: string;
  onVoiceNameChange: (value: string) => void;
  speechSupported: boolean;
  onPreview: () => void;
  /** When true, controls sit behind a disclosure (keeps setup/live lighter). */
  collapsed?: boolean;
};

/** Friendly label for summaries — never raw ids like ef_dora. */
function friendlyVoiceLabel(
  voiceName: string,
  voices: VoiceOption[],
  noneLabel: string,
): string {
  if (!voiceName) return noneLabel;
  const found = voices.find((v) => v.name === voiceName);
  const raw = found?.label || voiceName;

  // "Kokoro Dora (ES · mujer)" → "Kokoro Dora (ES)"
  const kokoro = raw.match(/^(Kokoro\s+\S+)\s*\(([^)·]+)/i);
  if (kokoro) return `${kokoro[1]} (${kokoro[2].trim()})`;

  if (/^(ef_|em_)/i.test(voiceName)) {
    const map: Record<string, string> = {
      ef_dora: "Kokoro Dora (ES)",
      em_alex: "Kokoro Alex (ES)",
      em_santa: "Kokoro Santa (ES)",
    };
    return map[voiceName] || "Kokoro (ES)";
  }

  const base = raw.split("(")[0]?.trim() || raw;
  return base.length > 28 ? `${base.slice(0, 27)}…` : base;
}

function Controls({
  voiceOut,
  onVoiceOutChange,
  voices,
  voiceName,
  onVoiceNameChange,
  speechSupported,
  onPreview,
}: Omit<Props, "collapsed">) {
  const { t } = useLocale();
  return (
    <div className="voice-bar">
      <label className="toggle">
        <input
          type="checkbox"
          checked={voiceOut}
          onChange={(e) => onVoiceOutChange(e.target.checked)}
          disabled={!speechSupported}
        />
        <span>{t("voice.speakReplies")}</span>
      </label>

      <label className="voice-select">
        <span className="sr-only">{t("voice.selectAria")}</span>
        <select
          value={voiceName}
          aria-label={t("voice.selectAria")}
          disabled={!speechSupported || voices.length === 0}
          onChange={(e) => onVoiceNameChange(e.target.value)}
        >
          {voices.length === 0 ? (
            <option value="">{t("voice.loading")}</option>
          ) : (
            voices.map((v) => (
              <option key={`${v.name}-${v.lang}`} value={v.name}>
                {v.label}
              </option>
            ))
          )}
        </select>
      </label>

      <button
        type="button"
        className="secondary"
        disabled={!voiceOut || !voiceName}
        onClick={onPreview}
      >
        {t("voice.preview")}
      </button>
    </div>
  );
}

export default function VoiceControls(props: Props) {
  const { t } = useLocale();
  const { collapsed, voiceOut, voiceName, voices, ...rest } = props;
  if (!collapsed) {
    return (
      <Controls
        voiceOut={voiceOut}
        voiceName={voiceName}
        voices={voices}
        {...rest}
      />
    );
  }

  const name = friendlyVoiceLabel(voiceName, voices, t("voice.none"));
  const status = voiceOut
    ? t("voice.summaryOn", { name })
    : t("voice.summaryOff", { name });

  return (
    <details className="voice-details">
      <summary>
        <span className="voice-details__text">
          <span className="voice-details__kicker">{t("voice.settings")}</span>
          <span className="voice-details__status">{status}</span>
        </span>
        <span className="voice-details__chevron" aria-hidden>
          ▾
        </span>
      </summary>
      <Controls
        voiceOut={voiceOut}
        voiceName={voiceName}
        voices={voices}
        {...rest}
      />
    </details>
  );
}
