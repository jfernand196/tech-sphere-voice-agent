/** Server-side Kokoro TTS (WAV via /api/voice/tts) with browser fallback seam. */

export type KokoroVoiceOption = {
  name: string;
  lang: string;
  label: string;
};

export type TtsCapabilities = {
  mode: "kokoro" | "browser" | string;
  kokoro?: {
    ready?: boolean;
    default_voice?: string;
    voices?: Array<{ id: string; label: string }>;
  };
};

let cachedCaps: TtsCapabilities | null = null;
let currentAudio: HTMLAudioElement | null = null;
let audioToken = 0;

export async function loadTtsCapabilities(
  force = false,
): Promise<TtsCapabilities> {
  if (cachedCaps && !force) return cachedCaps;
  try {
    const res = await fetch("/api/voice/capabilities");
    if (!res.ok) throw new Error(res.statusText);
    cachedCaps = (await res.json()) as TtsCapabilities;
  } catch {
    cachedCaps = { mode: "browser" };
  }
  return cachedCaps;
}

export function getCachedTtsMode(): "kokoro" | "browser" {
  return cachedCaps?.mode === "kokoro" ? "kokoro" : "browser";
}

export function listKokoroVoices(): KokoroVoiceOption[] {
  const voices = cachedCaps?.kokoro?.voices ?? [];
  return voices.map((v) => ({
    name: v.id,
    lang: "es",
    label: v.label,
  }));
}

export function defaultKokoroVoice(): string {
  return cachedCaps?.kokoro?.default_voice || listKokoroVoices()[0]?.name || "ef_dora";
}

export function stopKokoroAudio(): void {
  audioToken += 1;
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.src = "";
    currentAudio = null;
  }
}

export async function speakWithKokoro(
  text: string,
  options: {
    voiceName?: string;
    onStart?: () => void;
  } = {},
): Promise<void> {
  const cleaned = text.trim();
  if (!cleaned) return;

  // Cancel any in-flight playback, then claim a fresh token for this utterance.
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.src = "";
    currentAudio = null;
  }
  const myToken = ++audioToken;

  const res = await fetch("/api/voice/tts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: cleaned,
      voice: options.voiceName || defaultKokoroVoice(),
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
      reject(new Error("No se pudo reproducir el audio de Kokoro."));
    };
    void audio.play().catch(reject);
  });
}
