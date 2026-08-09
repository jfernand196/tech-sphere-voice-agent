import { useEffect, useRef, useState } from "react";
import { endCall, listDemoPatients, sendTurn, startCall } from "../api";
import { errMessage } from "../errors";
import { canUseSpeechRecognition, listenOnce } from "../speech";
import type { ChatItem, CallSummary, DemoPatient } from "../types";

type Options = {
  onAgentReply?: (text: string) => void;
};

export function useCallSession({ onAgentReply }: Options = {}) {
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

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
    setBusy(true);
    try {
      const res = await startCall(patientName, procedure, diaPostop);
      setCallId(res.call_id);
      setMessages([{ role: "agent", content: res.greeting }]);
      onAgentReply?.(res.greeting);
    } catch (e) {
      setError(errMessage(e, "No se pudo iniciar la llamada"));
    } finally {
      setBusy(false);
    }
  }

  async function send(text?: string) {
    const message = (text ?? input).trim();
    if (!callId || !message) return;
    setError(null);
    setBusy(true);
    setInput("");
    setMessages((prev) => [...prev, { role: "patient", content: message }]);
    try {
      const turn = await sendTurn(callId, message);
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
      onAgentReply?.(turn.reply);
    } catch (e) {
      setError(errMessage(e, "Error en el turno"));
    } finally {
      setBusy(false);
    }
  }

  async function listenAndSend() {
    if (!canUseSpeechRecognition()) {
      setError("Tu navegador no soporta reconocimiento de voz. Usa Chrome y escribe el texto.");
      return;
    }
    setListening(true);
    setError(null);
    try {
      const transcript = await listenOnce("es-CO");
      if (transcript) await send(transcript);
    } catch (e) {
      setError(errMessage(e, "Error de micrófono"));
    } finally {
      setListening(false);
    }
  }

  async function end() {
    if (!callId) return;
    setBusy(true);
    try {
      const res = await endCall(callId);
      setSummary(res);
      setCallId(null);
      setMessages([]);
      setInput("");
    } catch (e) {
      setError(errMessage(e, "No se pudo cerrar la llamada"));
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
