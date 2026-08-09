import { useEffect, useRef, useState } from "react";
import { formatCaseLabel, humanizeDemoHint } from "../demoFormat";
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
  const selectedDemo = call.demoPatients.find((p) => p.id === call.selectedCaseId);
  const [editDetails, setEditDetails] = useState(false);

  function resetForNewCall() {
    voice.stopAgent();
    call.reset();
    setEditDetails(false);
  }

  const voiceProps = {
    voiceOut: voice.voiceOut,
    onVoiceOutChange: voice.setVoiceOut,
    voices: voice.voices,
    voiceName: voice.voiceName,
    onVoiceNameChange: voice.selectVoice,
    speechSupported: voice.speechSupported,
    onPreview: () =>
      voice.speakAgent(
        "Hola, soy tu agente de seguimiento post-operatorio. ¿Cómo te sientes hoy?",
      ),
  };

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
              ? "Elige un caso del kit o un paciente libre, y empieza la conversación."
              : phase === "live"
                ? "El agente adapta la charla, cita protocolos y decide si alertar."
                : "Revisa el resumen estructurado antes de una nueva llamada."}
          </p>
        </div>
      </header>

      {phase === "setup" || phase === "live" ? (
        <VoiceControls {...voiceProps} collapsed />
      ) : null}

      {phase === "setup" ? (
        <div className="setup-card enter">
          {call.demoPatients.length > 0 ? (
            <label className="field-block">
              Caso de demo (kit oficial)
              <select
                value={call.selectedCaseId}
                onChange={(e) => {
                  call.selectCase(e.target.value);
                  setEditDetails(false);
                }}
              >
                <option value="">Paciente libre (editar abajo)</option>
                {call.demoPatients.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre} · día {p.dia_postop} · {formatCaseLabel(p.label)}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {call.selectedCaseId && !editDetails ? (
            <div className="case-summary">
              <div>
                <strong>{call.patientName}</strong>
                <span>
                  {call.procedure} · día {call.diaPostop}
                  {selectedDemo
                    ? ` · ${formatCaseLabel(selectedDemo.label)}`
                    : ""}
                </span>
              </div>
              <button
                type="button"
                className="secondary"
                onClick={() => setEditDetails(true)}
              >
                Editar
              </button>
            </div>
          ) : (
            <>
              <div className="form-grid form-grid--2">
                <label>
                  Paciente
                  <input
                    value={call.patientName}
                    onChange={(e) => {
                      call.beginManualEdit();
                      call.setPatientName(e.target.value);
                    }}
                  />
                </label>
                <label>
                  Procedimiento
                  <input
                    value={call.procedure}
                    onChange={(e) => {
                      call.beginManualEdit();
                      call.setProcedure(e.target.value);
                    }}
                  />
                </label>
              </div>

              <label className="field-block">
                Día post-operatorio
                <input
                  type="number"
                  min={0}
                  max={60}
                  value={call.diaPostop}
                  onChange={(e) => {
                    call.beginManualEdit();
                    call.setDiaPostop(Number(e.target.value) || 0);
                  }}
                />
              </label>
            </>
          )}

          {call.demoHint ? (
            <p className="demo-hint">
              Pista para actuar al paciente (no se envía al modelo):{" "}
              {humanizeDemoHint(call.demoHint)}
              {selectedDemo?.ciudad || selectedDemo?.eps ? (
                <>
                  <br />
                  <span className="demo-hint__meta">
                    {[selectedDemo.ciudad, selectedDemo.eps].filter(Boolean).join(" · ")}
                  </span>
                </>
              ) : null}
            </p>
          ) : null}

          {call.error ? <p className="error banner-error">{call.error}</p> : null}

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
            <span
              className="call-meta__patient"
              title={call.callId ? `Sesión ${call.callId}` : undefined}
            >
              {call.patientName} · día {call.diaPostop}
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

          {call.error ? <p className="error banner-error">{call.error}</p> : null}
        </>
      ) : null}

      {phase === "ended" && call.summary ? (
        <CallSummaryCard summary={call.summary} onNewCall={resetForNewCall} />
      ) : null}

      {phase === "ended" && call.error ? (
        <p className="error banner-error">{call.error}</p>
      ) : null}
    </section>
  );
}
