import type { VoiceOption } from "../speech";

type Props = {
  voiceOut: boolean;
  onVoiceOutChange: (value: boolean) => void;
  voices: VoiceOption[];
  voiceName: string;
  onVoiceNameChange: (value: string) => void;
  speechSupported: boolean;
  onPreview: () => void;
};

export default function VoiceControls({
  voiceOut,
  onVoiceOutChange,
  voices,
  voiceName,
  onVoiceNameChange,
  speechSupported,
  onPreview,
}: Props) {
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
