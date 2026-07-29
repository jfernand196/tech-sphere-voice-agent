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
  score: number;
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

export async function loadVoices(): Promise<SpeechSynthesisVoice[]> {
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
      score: scoreVoice(v),
    }))
    .sort((a, b) => b.score - a.score);
}

export function pickBestSpanishVoice(
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

/** Soften text for TTS: less “robot reading a protocol”. */
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

function splitForSpeech(text: string): string[] {
  const prepared = prepareSpokenText(text);
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
): Promise<void> {
  return new Promise((resolve, reject) => {
    const utter = new SpeechSynthesisUtterance(text);
    utter.lang = voice?.lang || lang;
    if (voice) utter.voice = voice;
    // Slightly slower + neutral pitch reads more “clínico / humano”
    utter.rate = 0.92;
    utter.pitch = 1.02;
    utter.volume = 1;
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

export type SpeakOptions = {
  lang?: string;
  voiceName?: string;
};

export async function speak(text: string, options: SpeakOptions = {}): Promise<void> {
  if (!canUseSpeechSynthesis() || !text.trim()) return;

  const lang = options.lang ?? "es-CO";
  const voices = await loadVoices();
  const voice = pickBestSpanishVoice(voices, options.voiceName);

  // Chrome sometimes stalls if cancel() isn't followed by a tiny gap
  window.speechSynthesis.cancel();
  await new Promise((r) => window.setTimeout(r, 40));

  const chunks = splitForSpeech(text);
  speakChain = speakChain
    .catch(() => undefined)
    .then(async () => {
      for (const chunk of chunks) {
        await speakChunk(chunk, voice, lang);
        await new Promise((r) => window.setTimeout(r, 120));
      }
    });
  return speakChain;
}

export function listenOnce(lang = "es-CO"): Promise<string> {
  return new Promise((resolve, reject) => {
    const Ctor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Ctor) {
      reject(new Error("Web Speech API no disponible en este navegador"));
      return;
    }
    // Pause TTS so recognition isn't fighting the speaker
    if (canUseSpeechSynthesis()) window.speechSynthesis.cancel();

    const recognition = new Ctor();
    recognition.lang = lang;
    recognition.interimResults = false;
    recognition.continuous = false;
    recognition.onresult = (event) => {
      const transcript = event.results[0]?.[0]?.transcript?.trim() || "";
      resolve(transcript);
    };
    recognition.onerror = (event) => reject(new Error(event.error));
    recognition.onend = () => undefined;
    recognition.start();
  });
}
