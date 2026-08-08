import { useEffect, useRef } from "react";
import { useAgentVoice } from "../hooks/useAgentVoice";
import { useCallSession } from "../hooks/useCallSession";
import CallSummaryCard from "./CallSummaryCard";
import ChatMessage from "./ChatMessage";
import VoiceControls from "./VoiceControls";

export default function CallPanel() {
  const voice = useAgentVoice();
  const speakRef = useRef(voice.speakAgent);
  useEffect(() => {
    speakRef.current = voice.speakAgent;
  }, [voice.speakAgent]);

  const call = useCallSession({
    onAgentReply: (text) => speakRef.current(text),
  });

  const phase = call.callId ? "live" : call.summary ? "ended" : "setup";

  function resetForNewCall() {
    voice.stopAgent();
    call.reset();
  }

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <div className="title-row">
            <h2>Llamada de seguimiento</h2>
            {phase === "live" ? <span className="live-pill">En curso</span> : null}
            {phase === "ended" ? <span className="ended-pill">Finalizada</span> : null}
          </div>
          <p>
            {phase === "setup"
              ? "Configura al paciente y empieza la conversación por texto o voz."
              : phase === "live"
                ? "El agente adapta la charla, cita protocolos y decide si alertar."
                : "Revisa el resumen estructurado antes de una nueva llamada."}
          </p>
        </div>
      </header>

      <VoiceControls
        voiceOut={voice.voiceOut}
        onVoiceOutChange={voice.setVoiceOut}
        voices={voice.voices}
        voiceName={voice.voiceName}
        onVoiceNameChange={voice.selectVoice}
        speechSupported={voice.speechSupported}
        onPreview={() =>
          voice.speakAgent(
            "Hola, soy tu agente de seguimiento post-operatorio. ¿Cómo te sientes hoy?",
          )
        }
      />

      {phase === "setup" ? (
        <div className="setup-card enter">
          <div className="form-grid form-grid--2">
            <label>
              Paciente
              <input
                value={call.patientName}
                onChange={(e) => call.setPatientName(e.target.value)}
              />
            </label>
            <label>
              Procedimiento
              <input
                value={call.procedure}
                onChange={(e) => call.setProcedure(e.target.value)}
              />
            </label>
          </div>
          <button
            type="button"
            className="btn-block"
            onClick={() => void call.start()}
            disabled={call.busy}
          >
            Iniciar llamada
          </button>
        </div>
      ) : null}

      {phase === "live" ? (
        <>
          <div className="call-meta">
            <span className="call-id">
              Sesión <code>{call.callId?.slice(0, 8)}</code>
            </span>
            <button
              type="button"
              className="danger"
              onClick={() => {
                voice.stopAgent();
                void call.end();
              }}
              disabled={call.busy}
            >
              Colgar
            </button>
          </div>

          <div className="chat" aria-live="polite">
            {call.messages.map((m, idx) => (
              <ChatMessage key={`${m.role}-${idx}`} message={m} />
            ))}
            <div ref={call.bottomRef} />
          </div>

          <div className="composer">
            <input
              value={call.input}
              onChange={(e) => call.setInput(e.target.value)}
              placeholder="Escribe lo que dice el paciente…"
              onKeyDown={(e) => {
                if (e.key === "Enter") void call.send();
              }}
              disabled={call.busy}
            />
            <button
              type="button"
              className="secondary"
              onClick={() => void call.send()}
              disabled={call.busy || !call.input.trim()}
            >
              Enviar
            </button>
            <button
              type="button"
              onClick={() => void call.listenAndSend()}
              disabled={call.busy || call.listening}
            >
              {call.listening ? "Escuchando…" : "Hablar"}
            </button>
          </div>
        </>
      ) : null}

      {phase === "ended" && call.summary ? (
        <CallSummaryCard summary={call.summary} onNewCall={resetForNewCall} />
      ) : null}

      {call.error ? <p className="error banner-error">{call.error}</p> : null}
    </section>
  );
}
