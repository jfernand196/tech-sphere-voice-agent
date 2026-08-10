import { useEffect, useRef, useState } from "react";
import { endCall, listDemoPatients, sendTurn, startCall } from "../api";
import { agentChatItemFromTurn } from "../callFormat";
import { errMessage } from "../errors";
import { useLocale } from "../i18n/LocaleContext";
import { canUseSpeechRecognition, listenOnce } from "../speech";
import type { ChatItem, CallSummary, DemoPatient } from "../types";

type Options = {
  /** Speak reply; return E2E ms when speechEndedAt was provided. */
  onAgentReply?: (text: string, speechEndedAt?: number) => Promise<number | undefined> | void;
};

export function useCallSession({ onAgentReply }: Options = {}) {
  const { t } = useLocale();
  const [demoPatients, setDemoPatients] = useState<DemoPatient[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState("");
  const [patientName, setPatientName] = useState("Ana Pérez");
  const [procedure, setProcedure] = useState("colecistectomía");
  const [diaPostop, setDiaPostop] = useState(3);
  const [demoHint, setDemoHint] = useState("");
  const [callId, setCallId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [listening, setListening] = useState(false);
  const [summary, setSummary] = useState<CallSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const e2eSamplesRef = useRef<number[]>([]);

  function clearE2eSamples() {
    e2eSamplesRef.current = [];
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, listening, busy]);

  useEffect(() => {
    void listDemoPatients()
      .then((rows) => {
        setDemoPatients(rows);
        if (rows[0]) applyCase(rows[0]);
      })
      .catch(() => {
        // Manual form still works without the selector catalog.
      });
  }, []);

  function applyCase(row: DemoPatient) {
    setSelectedCaseId(row.id);
    setPatientName(row.nombre);
    setProcedure(row.procedimiento);
    setDiaPostop(row.dia_postop);
    setDemoHint(row.demo_hint || "");
  }

  function selectCase(caseId: string) {
    setSelectedCaseId(caseId);
    if (!caseId) {
      setDemoHint("");
      return;
    }
    const row = demoPatients.find((p) => p.id === caseId);
    if (row) applyCase(row);
  }

  /** Switch to free-form editing; keep current field values. */
  function beginManualEdit() {
    setSelectedCaseId("");
    setDemoHint("");
  }

  async function start() {
    setError(null);
    setSummary(null);
    clearE2eSamples();
    setBusy(true);
    try {
      const res = await startCall(patientName, procedure, diaPostop);
      setCallId(res.call_id);
      setMessages([{ role: "agent", content: res.greeting }]);
      void onAgentReply?.(res.greeting);
    } catch (e) {
      setError(errMessage(e, t("call.errorStart")));
    } finally {
      setBusy(false);
    }
  }

  async function send(text?: string, speechEndedAt?: number) {
    const message = (text ?? input).trim();
    if (!callId || !message) return;
    setError(null);
    setBusy(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "patient", content: message }]);
    try {
      const turn = await sendTurn(callId, message);
      const spoken = await onAgentReply?.(turn.reply, speechEndedAt);
      const e2eMs = typeof spoken === "number" ? spoken : undefined;
      if (e2eMs != null) e2eSamplesRef.current.push(e2eMs);
      setMessages((prev) => [...prev, agentChatItemFromTurn(turn, e2eMs)]);
    } catch (e) {
      setError(errMessage(e, t("call.errorTurn")));
    } finally {
      setBusy(false);
    }
  }

  async function listenAndSend() {
    if (!canUseSpeechRecognition()) {
      setError(t("call.errorNoSpeechApi"));
      return;
    }
    setListening(true);
    setError(null);
    try {
      const { transcript, endedAt } = await listenOnce("es-CO");
      // Drop listening UI as soon as STT ends — not during agent TTS.
      setListening(false);
      if (transcript) await send(transcript, endedAt);
    } catch (e) {
      setError(errMessage(e, t("call.errorMic")));
      setListening(false);
    }
  }

  async function end() {
    if (!callId) return;
    setBusy(true);
    setError(null);
    try {
      const res = await endCall(callId, e2eSamplesRef.current);
      setSummary(res);
      setCallId(null);
      setMessages([]);
      setInput("");
      clearE2eSamples();
    } catch (e) {
      setError(errMessage(e, t("call.errorEnd")));
    } finally {
      setBusy(false);
    }
  }

  function reset() {
    setCallId(null);
    setMessages([]);
    setInput("");
    setSummary(null);
    setError(null);
    setListening(false);
    setBusy(false);
    clearE2eSamples();
  }

  return {
    demoPatients,
    selectedCaseId,
    selectCase,
    beginManualEdit,
    patientName,
    setPatientName,
    procedure,
    setProcedure,
    diaPostop,
    setDiaPostop,
    demoHint,
    callId,
    input,
    setInput,
    messages,
    busy,
    listening,
    summary,
    error,
    bottomRef,
    start,
    send,
    listenAndSend,
    end,
    reset,
  };
}
