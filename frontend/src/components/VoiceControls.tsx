import { useLocale } from "../i18n/LocaleContext";
import type { TtsEngine } from "../kokoroTts";
import type { VoiceOption } from "../speech";
import Disclosure from "./Disclosure";

type Props = {
  voiceOut: boolean;
  onVoiceOutChange: (value: boolean) => void;
  voices: VoiceOption[];
  voiceName: string;
  onVoiceNameChange: (value: string) => void;
  speechSupported: boolean;
  onPreview: () => void;
  ttsEngine: TtsEngine;
  onTtsEngineChange: (engine: TtsEngine) => void;
  kokoroReady: boolean;
  /** When true, controls sit behind a disclosure (keeps setup/live lighter). */
  collapsed?: boolean;
};

const KOKORO_SHORT: Record<string, string> = {
  ef_dora: "Dora",
  em_alex: "Alex",
  em_santa: "Santa",
};

/** Friendly label for summaries — never raw ids like ef_dora. */
function friendlyVoiceLabel(
  voiceName: string,
  voices: VoiceOption[],
  noneLabel: string,
  engine: TtsEngine,
): string {
  if (!voiceName) return noneLabel;
  const found = voices.find((v) => v.name === voiceName);
  const raw = found?.label || voiceName;

  if (engine === "kokoro" || /^(ef_|em_)/i.test(voiceName)) {
    if (KOKORO_SHORT[voiceName]) return KOKORO_SHORT[voiceName];
    // "Kokoro Dora (ES · mujer)" → "Dora"
    const given = raw.match(/^Kokoro\s+(\S+)/i);
    if (given) return given[1];
    return raw.split("(")[0]?.trim() || "Kokoro";
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
  ttsEngine,
  onTtsEngineChange,
  kokoroReady,
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

      {kokoroReady ? (
        <label className="voice-select">
          <span className="voice-select__label">{t("voice.engineLabel")}</span>
          <select
            value={ttsEngine}
            aria-label={t("voice.engineAria")}
            onChange={(e) => onTtsEngineChange(e.target.value as TtsEngine)}
          >
            <option value="browser">{t("voice.engineBrowser")}</option>
            <option value="kokoro">{t("voice.engineKokoro")}</option>
          </select>
        </label>
      ) : null}

      <label className="voice-select">
        <span className="voice-select__label">{t("voice.voiceLabel")}</span>
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
  const {
    collapsed,
    voiceOut,
    voiceName,
    voices,
    ttsEngine,
    ...rest
  } = props;
  if (!collapsed) {
    return (
      <Controls
        voiceOut={voiceOut}
        voiceName={voiceName}
        voices={voices}
        ttsEngine={ttsEngine}
        {...rest}
      />
    );
  }

  const name = friendlyVoiceLabel(
    voiceName,
    voices,
    t("voice.none"),
    ttsEngine,
  );
  const engineLabel =
    ttsEngine === "kokoro"
      ? t("voice.engineKokoroShort")
      : t("voice.engineBrowserShort");
  const status = voiceOut
    ? t("voice.summaryOnEngine", { engine: engineLabel, name })
    : t("voice.summaryOffEngine", { engine: engineLabel, name });

  return (
    <Disclosure
      className="disclosure--voice"
      kicker={t("voice.settings")}
      title={status}
    >
      <Controls
        voiceOut={voiceOut}
        voiceName={voiceName}
        voices={voices}
        ttsEngine={ttsEngine}
        {...rest}
      />
    </Disclosure>
  );
}
