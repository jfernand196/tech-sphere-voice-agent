type SpeechRecognitionLike = {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};

type SpeechRecognitionEventLike = {
  results: ArrayLike<ArrayLike<{ transcript: string }>>;
};

export type VoiceOption = {
  name: string;
  lang: string;
  label: string;
};

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionLike;
    webkitSpeechRecognition?: new () => SpeechRecognitionLike;
  }
}

const PREFERRED_VOICE_HINTS = [
  "google español de estados unidos",
  "google español",
  "microsoft sabina",
  "microsoft helena",
  "microsoft elvira",
  "paulina",
  "mónica",
  "monica",
  "luciana",
  "spanish",
  "español",
];

let cachedVoices: SpeechSynthesisVoice[] = [];
let speakChain: Promise<void> = Promise.resolve();
/** Bumped to cancel in-flight multi-chunk TTS (hang up / new utterance). */
let speakToken = 0;

export function canUseSpeechRecognition(): boolean {
  return Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
}

export function canUseSpeechSynthesis(): boolean {
  return typeof window !== "undefined" && "speechSynthesis" in window;
}

function scoreVoice(voice: SpeechSynthesisVoice): number {
  const name = voice.name.toLowerCase();
  const lang = voice.lang.toLowerCase();
  let score = 0;

  if (lang.startsWith("es")) score += 40;
  if (lang.includes("es-419") || lang.includes("es-mx") || lang.includes("es-us")) {
    score += 25;
  } else if (lang.includes("es-co")) {
    score += 30;
  } else if (lang.includes("es-es")) {
    score += 15;
  }

  for (let i = 0; i < PREFERRED_VOICE_HINTS.length; i += 1) {
    if (name.includes(PREFERRED_VOICE_HINTS[i])) {
      score += 50 - i;
      break;
    }
  }

  // Neural / enhanced voices when the OS exposes them
  if (name.includes("neural") || name.includes("natural") || name.includes("premium")) {
    score += 20;
  }
  if (voice.localService) score += 5;
  // Prefer female-sounding clinical assistants when hinted in the name
  if (/(female|mujer|sabina|paulina|m[oó]nica|helena|elvira|luciana)/i.test(name)) {
    score += 8;
  }

  return score;
}

async function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  if (!canUseSpeechSynthesis()) return [];

  const current = window.speechSynthesis.getVoices();
  if (current.length) {
    cachedVoices = current;
    return current;
  }

  return new Promise((resolve) => {
    const done = () => {
      cachedVoices = window.speechSynthesis.getVoices();
      resolve(cachedVoices);
    };
    window.speechSynthesis.addEventListener("voiceschanged", done, { once: true });
    // Safari / some Chromium builds never fire voiceschanged
    window.setTimeout(done, 400);
  });
}

export async function listSpanishVoices(): Promise<VoiceOption[]> {
  const voices = await loadVoices();
  return voices
    .filter((v) => v.lang.toLowerCase().startsWith("es"))
    .map((v) => ({
      name: v.name,
      lang: v.lang,
      label: `${v.name} (${v.lang})`,
      _score: scoreVoice(v),
    }))
    .sort((a, b) => b._score - a._score)
    .map(({ name, lang, label }) => ({ name, lang, label }));
}

function pickBestSpanishVoice(
  voices: SpeechSynthesisVoice[],
  preferredName?: string,
): SpeechSynthesisVoice | null {
  if (!voices.length) return null;
  if (preferredName) {
    const exact = voices.find((v) => v.name === preferredName);
    if (exact) return exact;
  }
  const ranked = [...voices].sort((a, b) => scoreVoice(b) - scoreVoice(a));
  return ranked.find((v) => v.lang.toLowerCase().startsWith("es")) ?? ranked[0] ?? null;
}

/** Soften text for TTS (Kokoro + browser): less “robot reading a protocol”. */
export function prepareSpokenText(text: string): string {
  return text
    .replace(/\b(\d+)\.(\d+)\s*°?\s*C\b/gi, "$1 coma $2 grados")
    .replace(/\b(\d+)\s*°?\s*C\b/gi, "$1 grados")
    .replace(/\bP50\b/g, "P cincuenta")
    .replace(/\bP95\b/g, "P noventa y cinco")
    .replace(/[•·]/g, ",")
    .replace(/\s+/g, " ")
    .replace(/\s+([,?!.])/g, "$1")
    .trim();
}

function splitForSpeech(prepared: string): string[] {
  const parts = prepared
    .split(/(?<=[.!?])\s+/)
    .map((p) => p.trim())
    .filter(Boolean);
  return parts.length ? parts : [prepared];
}

function speakChunk(
  text: string,
  voice: SpeechSynthesisVoice | null,
  lang: string,
  onStart?: () => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = voice?.lang || lang;
    if (voice) utter.voice = voice;
    // Slightly slower + neutral pitch reads more “clínico / humano”
    utter.rate = 0.92;
    utter.pitch = 1.02;
    utter.volume = 1;
    if (onStart) {
      utter.onstart = () => onStart();
    }
    utter.onend = () => resolve();
    utter.onerror = (event) => {
      if (event.error === "interrupted" || event.error === "canceled") {
        resolve();
        return;
      }
      reject(new Error(event.error));
    };
    window.speechSynthesis.speak(utter);
  });
}

type SpeakOptions = {
  lang?: string;
  voiceName?: string;
  /** Fires when the first audio chunk actually starts (challenge E2E end mark). */
  onStart?: () => void;
};

export function stopSpeaking(): void {
  speakToken += 1;
  void import("./kokoroTts").then((m) => m.stopKokoroAudio());
  if (canUseSpeechSynthesis()) {
    window.speechSynthesis.cancel();
  }
}

async function speakBrowser(text: string, options: SpeakOptions = {}): Promise<void> {
  if (!canUseSpeechSynthesis() || !text.trim()) return;

  const lang = options.lang ?? "es-CO";
  const voices = await loadVoices();
  const voice = pickBestSpanishVoice(voices, options.voiceName);
  const myToken = ++speakToken;

  // Chrome sometimes stalls if cancel() isn't followed by a tiny gap
  window.speechSynthesis.cancel();
  await new Promise((r) => window.setTimeout(r, 40));
  if (myToken !== speakToken) return;

  const chunks = splitForSpeech(text);
  let started = false;
  speakChain = speakChain
    .catch(() => undefined)
    .then(async () => {
      for (const chunk of chunks) {
        if (myToken !== speakToken) return;
        await speakChunk(chunk, voice, lang, () => {
          if (!started) {
            started = true;
            options.onStart?.();
          }
        });
        if (myToken !== speakToken) return;
        await new Promise((r) => window.setTimeout(r, 120));
      }
    });
  return speakChain;
}

export async function speak(text: string, options: SpeakOptions = {}): Promise<void> {
  const prepared = prepareSpokenText(text);
  if (!prepared) return;

  const { getCachedTtsMode, speakWithKokoro, loadTtsCapabilities } = await import(
    "./kokoroTts"
  );
  await loadTtsCapabilities();

  if (getCachedTtsMode() === "kokoro") {
    try {
      await speakWithKokoro(prepared, {
        voiceName: options.voiceName,
        onStart: options.onStart,
      });
      return;
    } catch (err) {
      console.warn("Kokoro TTS failed; falling back to browser speechSynthesis", err);
    }
  }

  return speakBrowser(prepared, options);
}

export type ListenResult = {
  transcript: string;
  /** performance.now() when final speech result arrived (patient finished speaking). */
  endedAt: number;
};

function speechErrorMessage(code: string): string {
  const map: Record<string, string> = {
    "no-speech":
      "No se escuchó voz. Pulsa Hablar, espera el permiso del micrófono y habla enseguida (Chrome/Edge).",
    "audio-capture": "No hay micrófono disponible o está en uso por otra app.",
    "not-allowed":
      "Permiso de micrófono denegado. En la barra de la URL, permite el micrófono y recarga.",
    "network": "El reconocimiento de voz del navegador falló (red). Prueba de nuevo o escribe el mensaje.",
    "aborted": "Escucha cancelada.",
    "service-not-allowed": "Este navegador no permite reconocimiento de voz aquí. Usa Chrome o Edge.",
  };
  return map[code] || `Error de voz: ${code}`;
}

export function listenOnce(lang = "es-CO"): Promise<ListenResult> {
  return new Promise((resolve, reject) => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Ctor) {
      reject(new Error("Web Speech API no disponible en este navegador. Usa Chrome o Edge."));
      return;
    }
    // Pause TTS so recognition isn't fighting the speaker
    stopSpeaking();

    const recognition = new Ctor();
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.continuous = false;
    let settled = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim() || "";
      if (!transcript) {
        reject(new Error(speechErrorMessage("no-speech")));
        return;
      }
      settled = true;
      resolve({ transcript, endedAt: performance.now() });
    };
    recognition.onerror = (event) => reject(new Error(speechErrorMessage(event.error)));
    recognition.onend = () => {
      if (!settled) {
        reject(new Error(speechErrorMessage("no-speech")));
      }
    };
    recognition.start();
  });
}
