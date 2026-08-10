import { useLocale } from "../i18n/LocaleContext";
import type { TtsEngine } from "../serverTts";
import type { VoiceOption } from "../speech";
import Disclosure from "./Disclosure";

type Props = {
  voices: VoiceOption[];
  voiceName: string;
  onVoiceNameChange: (value: string) => void;
  speechSupported: boolean;
  onPreview: () => void;
  ttsEngine: TtsEngine;
  onTtsEngineChange: (engine: TtsEngine) => void;
  kokoroReady: boolean;
  piperReady: boolean;
  /** When true, controls sit behind a disclosure (keeps setup/live lighter). */
  collapsed?: boolean;
};

const KOKORO_SHORT: Record<string, string> = {
  ef_dora: "Dora",
  em_alex: "Alex",
  em_santa: "Santa",
};

const PIPER_SHORT: Record<string, string> = {
  "es_MX-ald-medium": "Ald",
  "es_MX-claude-high": "Claude",
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
    const given = raw.match(/^Kokoro\s+(\S+)/i);
    if (given) return given[1];
    return raw.split("(")[0]?.trim() || "Kokoro";
  }

  if (engine === "piper" || /^es_[A-Z]{2}-/i.test(voiceName)) {
    if (PIPER_SHORT[voiceName]) return PIPER_SHORT[voiceName];
    const given = raw.match(/^Piper\s+(\S+)/i);
    if (given) return given[1];
    return raw.split("(")[0]?.trim() || "Piper";
  }

  const base = raw.split("(")[0]?.trim() || raw;
  return base.length > 28 ? `${base.slice(0, 27)}…` : base;
}

function engineShortLabel(
  engine: TtsEngine,
  t: (key: "voice.engineBrowserShort" | "voice.engineKokoroShort" | "voice.enginePiperShort") => string,
): string {
  if (engine === "kokoro") return t("voice.engineKokoroShort");
  if (engine === "piper") return t("voice.enginePiperShort");
  return t("voice.engineBrowserShort");
}

function Controls({
  voices,
  voiceName,
  onVoiceNameChange,
  speechSupported,
  onPreview,
  ttsEngine,
  onTtsEngineChange,
  kokoroReady,
  piperReady,
}: Omit<Props, "collapsed">) {
  const { t } = useLocale();
  const showEngineSelect = kokoroReady || piperReady;
  return (
    <div className="voice-bar">
      {showEngineSelect ? (
        <label className="voice-select">
          <span className="voice-select__label">{t("voice.engineLabel")}</span>
          <select
            value={ttsEngine}
            aria-label={t("voice.engineAria")}
            onChange={(e) => onTtsEngineChange(e.target.value as TtsEngine)}
          >
            <option value="browser">{t("voice.engineBrowser")}</option>
            {kokoroReady ? (
              <option value="kokoro">{t("voice.engineKokoro")}</option>
            ) : null}
            {piperReady ? (
              <option value="piper">{t("voice.enginePiper")}</option>
            ) : null}
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
        disabled={!voiceName}
        onClick={onPreview}
      >
        {t("voice.preview")}
      </button>
    </div>
  );
}

export default function VoiceControls(props: Props) {
  const { t } = useLocale();
  const { collapsed, voiceName, voices, ttsEngine, ...rest } = props;
  if (!collapsed) {
    return (
      <Controls
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
  const engineLabel = engineShortLabel(ttsEngine, t);
  const status = t("voice.summaryEngine", { engine: engineLabel, name });

  return (
    <Disclosure
      className="disclosure--voice"
      kicker={t("voice.settings")}
      title={status}
    >
      <Controls
        voiceName={voiceName}
        voices={voices}
        ttsEngine={ttsEngine}
        {...rest}
      />
    </Disclosure>
  );
}
