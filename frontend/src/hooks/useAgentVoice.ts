import { useEffect, useState } from "react";
import {
  canUseSpeechSynthesis,
  listSpanishVoices,
  speak,
  stopSpeaking,
  type VoiceOption,
} from "../speech";
import {
  defaultKokoroVoice,
  getPreferredTtsEngine,
  isKokoroAvailable,
  listKokoroVoices,
  loadTtsCapabilities,
  setPreferredTtsEngine,
  type TtsEngine,
} from "../kokoroTts";

const VOICE_STORAGE_KEY = "tsva.voiceName";
const BROWSER_VOICE_KEY = "tsva.browserVoiceName";
const KOKORO_VOICE_KEY = "tsva.kokoroVoiceName";

function voiceKeyFor(engine: TtsEngine): string {
  return engine === "kokoro" ? KOKORO_VOICE_KEY : BROWSER_VOICE_KEY;
}

export function useAgentVoice() {
  const [voiceOut, setVoiceOut] = useState(true);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [ttsEngine, setTtsEngine] = useState<TtsEngine>("browser");
  const [kokoroReady, setKokoroReady] = useState(false);
  const [voiceName, setVoiceName] = useState("");

  useEffect(() => {
    void (async () => {
      await loadTtsCapabilities();
      const ready = isKokoroAvailable();
      setKokoroReady(ready);
      const preferred = getPreferredTtsEngine();
      const engine: TtsEngine =
        preferred === "kokoro" && ready ? "kokoro" : "browser";
      setTtsEngine(engine);
      await applyEngine(engine);
    })();
  }, []);

  async function applyEngine(engine: TtsEngine) {
    if (engine === "kokoro" && isKokoroAvailable()) {
      const kokoro = listKokoroVoices();
      setVoices(kokoro);
      const saved =
        localStorage.getItem(voiceKeyFor("kokoro")) ||
        localStorage.getItem(VOICE_STORAGE_KEY) ||
        "";
      const next =
        (saved && kokoro.some((v) => v.name === saved) && saved) ||
        defaultKokoroVoice();
      setVoiceName(next);
      if (next) localStorage.setItem(voiceKeyFor("kokoro"), next);
      return;
    }

    const options = await listSpanishVoices();
    setVoices(options);
    const saved =
      localStorage.getItem(voiceKeyFor("browser")) ||
      localStorage.getItem(VOICE_STORAGE_KEY) ||
      "";
    const next =
      (saved && options.some((v) => v.name === saved) && saved) ||
      options[0]?.name ||
      "";
    setVoiceName(next);
    if (next) localStorage.setItem(voiceKeyFor("browser"), next);
  }

  async function selectEngine(engine: TtsEngine) {
    const next: TtsEngine =
      engine === "kokoro" && isKokoroAvailable() ? "kokoro" : "browser";
    setPreferredTtsEngine(next);
    setTtsEngine(next);
    stopSpeaking();
    await applyEngine(next);
  }

  function selectVoice(name: string) {
    setVoiceName(name);
    localStorage.setItem(voiceKeyFor(ttsEngine), name);
    localStorage.setItem(VOICE_STORAGE_KEY, name);
  }

  /**
   * Speak agent reply. If `speechEndedAt` is set (from STT), resolves with
   * challenge E2E latency ms (patient finished speaking → agent audio starts).
   */
  async function speakAgent(
    text: string,
    speechEndedAt?: number,
  ): Promise<number | undefined> {
    if (!voiceOut) return undefined;
    if (ttsEngine === "browser" && !canUseSpeechSynthesis()) return undefined;
    let e2e: number | undefined;
    await speak(text, {
      engine: ttsEngine,
      voiceName: voiceName || undefined,
      lang: "es-CO",
      onStart: () => {
        if (typeof speechEndedAt === "number") {
          e2e = Math.max(0, Math.round(performance.now() - speechEndedAt));
        }
      },
    });
    return e2e;
  }

  function stopAgent() {
    stopSpeaking();
  }

  function setVoiceOutAndMaybeStop(value: boolean) {
    setVoiceOut(value);
    if (!value) stopSpeaking();
  }

  return {
    voiceOut,
    setVoiceOut: setVoiceOutAndMaybeStop,
    voices,
    voiceName,
    selectVoice,
    speakAgent,
    stopAgent,
    ttsEngine,
    selectEngine,
    kokoroReady,
    speechSupported:
      ttsEngine === "kokoro" ? kokoroReady : canUseSpeechSynthesis(),
  };
}
