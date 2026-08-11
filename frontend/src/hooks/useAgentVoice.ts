import { useEffect, useState } from "react";
import {
  canUseSpeechSynthesis,
  listSpanishVoices,
  speak,
  stopSpeaking,
  type VoiceOption,
} from "../speech";
import {
  defaultServerVoice,
  getPreferredTtsEngine,
  isServerEngineAvailable,
  listServerVoices,
  loadTtsCapabilities,
  setPreferredTtsEngine,
  type ServerTtsEngine,
  type TtsEngine,
} from "../serverTts";

const VOICE_KEY: Record<TtsEngine, string> = {
  browser: "tsva.browserVoiceName",
  kokoro: "tsva.kokoroVoiceName",
  piper: "tsva.piperVoiceName",
};

function isServerEngine(engine: TtsEngine): engine is ServerTtsEngine {
  return engine === "kokoro" || engine === "piper";
}

export function useAgentVoice() {
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [ttsEngine, setTtsEngine] = useState<TtsEngine>("browser");
  const [kokoroReady, setKokoroReady] = useState(false);
  const [piperReady, setPiperReady] = useState(false);
  const [voiceName, setVoiceName] = useState("");

  useEffect(() => {
    void (async () => {
      await loadTtsCapabilities();
      setKokoroReady(isServerEngineAvailable("kokoro"));
      setPiperReady(isServerEngineAvailable("piper"));
      const preferred = getPreferredTtsEngine();
      const engine: TtsEngine = isServerEngineAvailable(preferred)
        ? preferred
        : "browser";
      setTtsEngine(engine);
      await applyEngine(engine);
    })();
  }, []);

  async function applyEngine(engine: TtsEngine) {
    const key = VOICE_KEY[engine];
    const options =
      isServerEngine(engine) && isServerEngineAvailable(engine)
        ? listServerVoices(engine)
        : await listSpanishVoices();
    const fallback =
      isServerEngine(engine) && isServerEngineAvailable(engine)
        ? defaultServerVoice(engine)
        : options[0]?.name || "";

    setVoices(options);
    const saved = localStorage.getItem(key) || "";
    const next =
      (saved && options.some((v) => v.name === saved) && saved) || fallback;
    setVoiceName(next);
    if (next) localStorage.setItem(key, next);
  }

  async function selectEngine(engine: TtsEngine) {
    const next: TtsEngine = isServerEngineAvailable(engine) ? engine : "browser";
    setPreferredTtsEngine(next);
    setTtsEngine(next);
    stopSpeaking();
    await applyEngine(next);
  }

  function selectVoice(name: string) {
    setVoiceName(name);
    localStorage.setItem(VOICE_KEY[ttsEngine], name);
  }

  /**
   * Speak agent reply. If `speechEndedAt` is set (from STT), resolves with
   * challenge E2E latency ms (patient finished speaking → agent audio starts).
   */
  async function speakAgent(
    text: string,
    speechEndedAt?: number,
  ): Promise<number | undefined> {
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

  return {
    voices,
    voiceName,
    selectVoice,
    speakAgent,
    stopAgent,
    ttsEngine,
    selectEngine,
    kokoroReady,
    piperReady,
    speechSupported:
      ttsEngine === "browser"
        ? canUseSpeechSynthesis()
        : isServerEngineAvailable(ttsEngine),
  };
}
