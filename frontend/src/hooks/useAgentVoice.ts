import { useEffect, useState } from "react";
import {
  canUseSpeechSynthesis,
  listSpanishVoices,
  speak,
  type VoiceOption,
} from "../speech";

const VOICE_STORAGE_KEY = "tsva.voiceName";

export function useAgentVoice() {
  const [voiceOut, setVoiceOut] = useState(true);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [voiceName, setVoiceName] = useState(
    () => localStorage.getItem(VOICE_STORAGE_KEY) ?? "",
  );

  useEffect(() => {
    void listSpanishVoices().then((options) => {
      setVoices(options);
      setVoiceName((current) => {
        if (current && options.some((v) => v.name === current)) return current;
        const best = options[0]?.name ?? "";
        if (best) localStorage.setItem(VOICE_STORAGE_KEY, best);
        return best;
      });
    });
  }, []);

  function selectVoice(name: string) {
    setVoiceName(name);
    localStorage.setItem(VOICE_STORAGE_KEY, name);
  }

  function speakAgent(text: string) {
    if (!voiceOut || !canUseSpeechSynthesis()) return;
    void speak(text, { voiceName: voiceName || undefined, lang: "es-CO" });
  }

  return {
    voiceOut,
    setVoiceOut,
    voices,
    voiceName,
    selectVoice,
    speakAgent,
    speechSupported: canUseSpeechSynthesis(),
  };
}
