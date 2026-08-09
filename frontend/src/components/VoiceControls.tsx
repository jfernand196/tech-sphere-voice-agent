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

function shortVoiceName(name: string): string {
  if (!name) return "sin voz";
  const base = name.split("(")[0]?.trim() || name;
  return base.length > 22 ? `${base.slice(0, 21)}…` : base;
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
  return (
    <div className="voice-bar">
      <label className="toggle">
        <input
          type="checkbox"
          checked={voiceOut}
          onChange={(e) => onVoiceOutChange(e.target.checked)}
          disabled={!speechSupported}
        />
        <span>Hablar respuestas</span>
      </label>

      <label className="voice-select">
        <span className="sr-only">Voz</span>
        <select
          value={voiceName}
          aria-label="Seleccionar voz"
          disabled={!speechSupported || voices.length === 0}
          onChange={(e) => onVoiceNameChange(e.target.value)}
        >
          {voices.length === 0 ? (
            <option value="">Cargando voces…</option>
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
        Probar voz
      </button>
    </div>
  );
}

export default function VoiceControls(props: Props) {
  const { collapsed, voiceOut, voiceName, ...rest } = props;
  if (!collapsed) {
    return (
      <Controls
        voiceOut={voiceOut}
        voiceName={voiceName}
        {...rest}
      />
    );
  }

  const summary = `Voz: ${shortVoiceName(voiceName)} · ${voiceOut ? "activada" : "apagada"}`;

  return (
    <details className="voice-details">
      <summary>{summary}</summary>
      <Controls voiceOut={voiceOut} voiceName={voiceName} {...rest} />
    </details>
  );
}
