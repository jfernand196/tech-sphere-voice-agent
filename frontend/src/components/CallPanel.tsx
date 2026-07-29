import { useEffect, useRef } from "react";
import { useAgentVoice } from "../hooks/useAgentVoice";
import { useCallSession } from "../hooks/useCallSession";
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

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <h2>Llamada de seguimiento</h2>
          <p>Texto primero; voz del navegador como adaptador (STT/TTS).</p>
        </div>
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
      </header>

      {!call.callId ? (
        <div className="form-grid">
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
          <button type="button" onClick={() => void call.start()} disabled={call.busy}>
            Iniciar llamada
          </button>
        </div>
      ) : (
        <div className="call-meta">
          <span>
            Call ID: <code>{call.callId}</code>
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
            Colgar y generar resumen
          </button>
        </div>
      )}

      <div className="chat">
        {call.messages.map((m, idx) => (
          <ChatMessage key={`${m.role}-${idx}`} message={m} />
        ))}
        <div ref={call.bottomRef} />
      </div>

      {call.callId ? (
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
      ) : null}

      {call.summary ? (
        <div className="summary">
          <h3>Resumen estructurado</h3>
          <p>{call.summary.summary_text}</p>
          <pre>{JSON.stringify(call.summary, null, 2)}</pre>
        </div>
      ) : null}

      {call.error ? <p className="error">{call.error}</p> : null}
    </section>
  );
}
