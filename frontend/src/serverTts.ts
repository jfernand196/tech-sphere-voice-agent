/** Server-side TTS (Kokoro / Piper WAV via /api/voice/tts) + browser preference. */

export type TtsEngine = "browser" | "kokoro" | "piper";
export type ServerTtsEngine = "kokoro" | "piper";

export type ServerVoiceOption = {
  name: string;
  lang: string;
  label: string;
};

type EngineCaps = {
  available?: boolean;
  default_voice?: string;
  voices?: Array<{ id: string; label: string }>;
};

export type TtsCapabilities = {
  engines?: {
    browser?: EngineCaps;
    kokoro?: EngineCaps;
    piper?: EngineCaps;
  };
};

const TTS_ENGINE_KEY = "tsva.ttsEngine";
const FALLBACK_VOICE: Record<ServerTtsEngine, string> = {
  kokoro: "ef_dora",
  piper: "es_MX-ald-medium",
};

let cachedCaps: TtsCapabilities | null = null;
let currentAudio: HTMLAudioElement | null = null;
let audioToken = 0;

function haltCurrentAudio(): void {
  if (!currentAudio) return;
  currentAudio.pause();
  currentAudio.src = "";
  currentAudio = null;
}

function engineCaps(engine: ServerTtsEngine): EngineCaps {
  return cachedCaps?.engines?.[engine] ?? {};
}

export async function loadTtsCapabilities(
  force = false,
): Promise<TtsCapabilities> {
  if (cachedCaps && !force) return cachedCaps;
  try {
    const res = await fetch("/api/voice/capabilities");
    if (!res.ok) throw new Error(res.statusText);
    cachedCaps = (await res.json()) as TtsCapabilities;
  } catch {
    cachedCaps = { engines: { browser: { available: true } } };
  }
  return cachedCaps;
}

export function isServerEngineAvailable(engine: TtsEngine): boolean {
  if (engine === "browser") return true;
  return Boolean(engineCaps(engine).available);
}

export function listServerVoices(engine: ServerTtsEngine): ServerVoiceOption[] {
  return (engineCaps(engine).voices ?? []).map((v) => ({
    name: v.id,
    lang: "es",
    label: v.label,
  }));
}

export function defaultServerVoice(engine: ServerTtsEngine): string {
  return (
    engineCaps(engine).default_voice ||
    listServerVoices(engine)[0]?.name ||
    FALLBACK_VOICE[engine]
  );
}

/**
 * User preference for TTS engine.
 * Default is browser (lower latency); Kokoro/Piper are opt-in when warmed.
 */
export function getPreferredTtsEngine(): TtsEngine {
  const saved = localStorage.getItem(TTS_ENGINE_KEY);
  if (saved === "kokoro" || saved === "piper" || saved === "browser") {
    if (saved !== "browser" && !isServerEngineAvailable(saved)) return "browser";
    return saved;
  }
  return "browser";
}

export function setPreferredTtsEngine(engine: TtsEngine): void {
  localStorage.setItem(TTS_ENGINE_KEY, engine);
}

export function stopServerTtsAudio(): void {
  audioToken += 1;
  haltCurrentAudio();
}

export async function speakWithServerTts(
  text: string,
  options: {
    engine: ServerTtsEngine;
    voiceName?: string;
    onStart?: () => void;
  },
): Promise<void> {
  const cleaned = text.trim();
  if (!cleaned) return;

  const myToken = ++audioToken;
  haltCurrentAudio();

  const res = await fetch("/api/voice/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: cleaned,
      engine: options.engine,
      voice: options.voiceName || defaultServerVoice(options.engine),
    }),
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  if (myToken !== audioToken) return;

  const blob = await res.blob();
  if (myToken !== audioToken) return;
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  currentAudio = audio;

  await new Promise<void>((resolve, reject) => {
    audio.onplay = () => options.onStart?.();
    audio.onended = () => {
      URL.revokeObjectURL(url);
      if (currentAudio === audio) currentAudio = null;
      resolve();
    };
    audio.onerror = () => {
      URL.revokeObjectURL(url);
      if (currentAudio === audio) currentAudio = null;
      reject(new Error(`No se pudo reproducir el audio de ${options.engine}.`));
    };
    void audio.play().catch(reject);
  });
}
