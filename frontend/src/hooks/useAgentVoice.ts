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
  getCachedTtsMode,
  listKokoroVoices,
  loadTtsCapabilities,
} from "../kokoroTts";

const VOICE_STORAGE_KEY = "tsva.voiceName";

export function useAgentVoice() {
  const [voiceOut, setVoiceOut] = useState(true);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [ttsMode, setTtsMode] = useState<"kokoro" | "browser">("browser");
  const [voiceName, setVoiceName] = useState(
    () => localStorage.getItem(VOICE_STORAGE_KEY) ?? "",
  );

  useEffect(() => {
    void (async () => {
      await loadTtsCapabilities();
      const mode = getCachedTtsMode();
      setTtsMode(mode);
      if (mode === "kokoro") {
        const kokoro = listKokoroVoices();
        setVoices(kokoro);
        setVoiceName((current) => {
          if (current && kokoro.some((v) => v.name === current)) return current;
          const best = defaultKokoroVoice();
          if (best) localStorage.setItem(VOICE_STORAGE_KEY, best);
          return best;
        });
        return;
      }
      const options = await listSpanishVoices();
      setVoices(options);
      setVoiceName((current) => {
        if (current && options.some((v) => v.name === current)) return current;
        const best = options[0]?.name ?? "";
        if (best) localStorage.setItem(VOICE_STORAGE_KEY, best);
        return best;
      });
    })();
  }, []);

  function selectVoice(name: string) {
    setVoiceName(name);
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
    if (ttsMode === "browser" && !canUseSpeechSynthesis()) return undefined;
    let e2e: number | undefined;
    await speak(text, {
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
    ttsMode,
    speechSupported: ttsMode === "kokoro" || canUseSpeechSynthesis(),
  };
}
