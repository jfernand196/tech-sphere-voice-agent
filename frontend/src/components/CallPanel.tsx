import { useEffect, useRef, useState } from "react";
import { endCall, sendTurn, startCall } from "../api";
import {
  canUseSpeechRecognition,
  canUseSpeechSynthesis,
  listSpanishVoices,
  listenOnce,
  speak,
  type VoiceOption,
} from "../speech";
import type { AgentTurnResponse, CallMessage, CallSummary } from "../types";

type ChatItem = CallMessage & { latency_ms?: number | null };

const VOICE_STORAGE_KEY = "tsva.voiceName";

export default function CallPanel() {
  const [patientName, setPatientName] = useState("Ana Pérez");
  const [procedure, setProcedure] = useState("apendicectomía");
  const [callId, setCallId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceOut, setVoiceOut] = useState(true);
  const [voices, setVoices] = useState<VoiceOption[]>([]);
  const [voiceName, setVoiceName] = useState(
    () => localStorage.getItem(VOICE_STORAGE_KEY) ?? "",
  );
  const [summary, setSummary] = useState<CallSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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

  function speakAgent(text: string) {
    if (!voiceOut) return;
    void speak(text, { voiceName: voiceName || undefined, lang: "es-CO" });
  }

  async function handleStart() {
    setError(null);
    setSummary(null);
    setBusy(true);
    try {
      const res = await startCall(patientName, procedure);
      setCallId(res.call_id);
      setMessages([{ role: "agent", content: res.greeting }]);
      speakAgent(res.greeting);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo iniciar la llamada");
    } finally {
      setBusy(false);
    }
  }

  async function handleSend(text?: string) {
    const message = (text ?? input).trim();
    if (!callId || !message) return;
    setError(null);
    setBusy(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "patient", content: message }]);
    try {
      const turn: AgentTurnResponse = await sendTurn(callId, message);
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          content: turn.reply,
          sources: turn.sources,
          escalate: turn.escalate,
          escalate_reason: turn.escalate_reason,
          patient_state: turn.patient_state,
          latency_ms: turn.latency_ms,
        },
      ]);
      speakAgent(turn.reply);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error en el turno");
    } finally {
      setBusy(false);
    }
  }

  async function handleListen() {
    if (!canUseSpeechRecognition()) {
      setError("Tu navegador no soporta reconocimiento de voz. Usa Chrome y escribe el texto.");
      return;
    }
    setListening(true);
    setError(null);
    try {
      const transcript = await listenOnce("es-CO");
      if (transcript) await handleSend(transcript);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de micrófono");
    } finally {
      setListening(false);
    }
  }

  async function handleEnd() {
    if (!callId) return;
    setBusy(true);
    try {
      const res = await endCall(callId);
      setSummary(res);
      setCallId(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cerrar la llamada");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h2>Llamada de seguimiento</h2>
          <p>Texto primero; voz del navegador como adaptador (STT/TTS).</p>
        </div>
        <div className="voice-controls">
          <label className="toggle">
            <input
              type="checkbox"
              checked={voiceOut}
              onChange={(e) => setVoiceOut(e.target.checked)}
              disabled={!canUseSpeechSynthesis()}
            />
            Hablar respuestas
          </label>
          <label className="voice-select">
            Voz
            <select
              value={voiceName}
              disabled={!canUseSpeechSynthesis() || voices.length === 0}
              onChange={(e) => {
                setVoiceName(e.target.value);
                localStorage.setItem(VOICE_STORAGE_KEY, e.target.value);
              }}
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
            onClick={() =>
              speakAgent(
                "Hola, soy tu agente de seguimiento post-operatorio. ¿Cómo te sientes hoy?",
              )
            }
          >
            Probar voz
          </button>
        </div>
      </header>

      {!callId ? (
        <div className="form-grid">
          <label>
            Paciente
            <input value={patientName} onChange={(e) => setPatientName(e.target.value)} />
          </label>
          <label>
            Procedimiento
            <input value={procedure} onChange={(e) => setProcedure(e.target.value)} />
          </label>
          <button type="button" onClick={handleStart} disabled={busy}>
            Iniciar llamada
          </button>
        </div>
      ) : (
        <div className="call-meta">
          <span>
            Call ID: <code>{callId}</code>
          </span>
          <button type="button" className="danger" onClick={handleEnd} disabled={busy}>
            Colgar y generar resumen
          </button>
        </div>
      )}

      <div className="chat">
        {messages.map((m, idx) => (
          <article key={idx} className={`bubble ${m.role}`}>
            <strong>{m.role === "agent" ? "Agente" : "Paciente"}</strong>
            <p>{m.content}</p>
            {m.escalate ? (
              <div className="alert">ALERTA HUMANO — {m.escalate_reason || "revisar caso"}</div>
            ) : null}
            {m.sources && m.sources.length > 0 ? (
              <ul className="sources">
                {m.sources.map((s) => (
                  <li key={s.chunk_id}>
                    <code>{s.title}</code> · {s.chunk_id}
                  </li>
                ))}
              </ul>
            ) : null}
            {typeof m.latency_ms === "number" ? (
              <small>{m.latency_ms} ms</small>
            ) : null}
          </article>
        ))}
        <div ref={bottomRef} />
      </div>

      {callId ? (
        <div className="composer">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Escribe lo que dice el paciente…"
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleSend();
            }}
            disabled={busy}
          />
          <button type="button" onClick={() => void handleSend()} disabled={busy || !input.trim()}>
            Enviar
          </button>
          <button type="button" onClick={() => void handleListen()} disabled={busy || listening}>
            {listening ? "Escuchando…" : "Hablar"}
          </button>
        </div>
      ) : null}

      {summary ? (
        <div className="summary">
          <h3>Resumen estructurado</h3>
          <p>{summary.summary_text}</p>
          <pre>{JSON.stringify(summary, null, 2)}</pre>
        </div>
      ) : null}

      {error ? <p className="error">{error}</p> : null}
    </section>
  );
}
