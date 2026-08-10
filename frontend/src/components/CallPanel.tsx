import { useEffect, useRef, useState } from "react";
import { lastTurnMetricsIndex } from "../callFormat";
import { demoHintBullets, formatCaseLabel } from "../demoFormat";
import { useAgentVoice } from "../hooks/useAgentVoice";
import { useCallSession } from "../hooks/useCallSession";
import { useLocale } from "../i18n/LocaleContext";
import CallComposer from "./CallComposer";
import CallSummaryCard from "./CallSummaryCard";
import ChatMessage from "./ChatMessage";
import ListenBanner from "./ListenBanner";
import VoiceControls from "./VoiceControls";

export default function CallPanel() {
  const { t } = useLocale();
  const voice = useAgentVoice();
  const speakRef = useRef(voice.speakAgent);
  useEffect(() => {
    speakRef.current = voice.speakAgent;
  }, [voice.speakAgent]);

  const call = useCallSession({
    onAgentReply: (text, speechEndedAt) => speakRef.current(text, speechEndedAt),
  });

  const phase = call.callId ? "live" : call.summary ? "ended" : "setup";
  const [editDetails, setEditDetails] = useState(false);
  const metricsHintAt = lastTurnMetricsIndex(call.messages);

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
    ttsEngine: voice.ttsEngine,
    onTtsEngineChange: (engine: "browser" | "kokoro" | "piper") => {
      void voice.selectEngine(engine);
    },
    kokoroReady: voice.kokoroReady,
    piperReady: voice.piperReady,
    // Preview keeps Spanish — agent language is not tied to UI locale.
    onPreview: () => voice.speakAgent(t("voice.previewText")),
  };

  const lead =
    phase === "setup"
      ? t("call.setupLead")
      : phase === "live"
        ? t("call.liveLead")
        : t("call.endedLead");

  return (
    <section className="panel">
      <header className="panel-header">
        <div>
          <div className="title-row">
            <h2>{t("call.title")}</h2>
            {phase === "live" ? <span className="live-pill">{t("call.live")}</span> : null}
            {phase === "ended" ? <span className="ended-pill">{t("call.ended")}</span> : null}
          </div>
          <p>{lead}</p>
        </div>
      </header>

      {phase === "setup" || phase === "live" ? (
        <VoiceControls {...voiceProps} collapsed />
      ) : null}

      {phase === "setup" ? (
        <div className="setup-card enter">
          {call.demoPatients.length > 0 ? (
            <div className="case-picker">
              <label className="field-block case-picker__field">
                {t("call.demoCase")}
                <select
                  value={call.selectedCaseId}
                  onChange={(e) => {
                    call.selectCase(e.target.value);
                    setEditDetails(false);
                  }}
                >
                  <option value="">{t("call.freePatient")}</option>
                  {call.demoPatients.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.nombre} · {t("call.day", { n: p.dia_postop })} ·{" "}
                      {formatCaseLabel(p.label, t)}
                    </option>
                  ))}
                </select>
              </label>
              {call.selectedCaseId && !editDetails ? (
                <button
                  type="button"
                  className="secondary case-picker__edit"
                  onClick={() => setEditDetails(true)}
                >
                  {t("call.edit")}
                </button>
              ) : null}
            </div>
          ) : null}

          {!call.selectedCaseId || editDetails ? (
            <>
              {editDetails && call.selectedCaseId ? (
                <p className="case-picker__note">{t("call.editDetails")}</p>
              ) : null}
              <div className="form-grid form-grid--2">
                <label>
                  {t("call.patient")}
                  <input
                    value={call.patientName}
                    onChange={(e) => {
                      call.beginManualEdit();
                      call.setPatientName(e.target.value);
                    }}
                  />
                </label>
                <label>
                  {t("call.procedure")}
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
                {t("call.diaPostop")}
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
          ) : null}

          <DemoHintCard hint={call.demoHint} title={t("call.demoHint")} />

          {call.error ? <p className="error banner-error">{call.error}</p> : null}

          <button
            type="button"
            className="btn-block"
            onClick={() => void call.start()}
            disabled={call.busy}
          >
            {t("call.start")}
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
              {call.patientName} · {t("call.day", { n: call.diaPostop })}
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
              {t("call.hangup")}
            </button>
          </div>

          <div className="chat" aria-live="polite">
            {call.messages.map((m, idx) => (
              <ChatMessage
                key={`${m.role}-${idx}`}
                message={m}
                showMetricsHint={idx === metricsHintAt}
              />
            ))}
            {call.listening ? <ListenBanner /> : null}
            <div ref={call.bottomRef} />
          </div>

          <CallComposer
            input={call.input}
            onInputChange={call.setInput}
            onSend={() => void call.send()}
            onListen={() => void call.listenAndSend()}
            busy={call.busy}
            listening={call.listening}
          />

          {call.error ? <p className="error banner-error">{call.error}</p> : null}
        </>
      ) : null}

      {phase === "ended" && call.summary ? (
        <CallSummaryCard summary={call.summary} onNewCall={resetForNewCall} />
      ) : null}
    </section>
  );
}

function DemoHintCard({ hint, title }: { hint: string; title: string }) {
  const bullets = demoHintBullets(hint, 3);
  if (!bullets.length) return null;
  return (
    <div className="demo-hint">
      <p className="demo-hint__title">{title}</p>
      <ul className="demo-hint__list">
        {bullets.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
