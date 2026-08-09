import type {
  AgentTurnResponse,
  CallSummary,
  DemoPatient,
  DocumentInfo,
} from "./types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export function getHealth() {
  return request<{
    status: string;
    model_id: string;
    llm_provider: string;
    llm_ready?: boolean;
    llm_detail?: string;
  }>("/health");
}

export function startCall(
  patient_name: string,
  procedure: string,
  dia_postop: number,
) {
  return request<{ call_id: string; greeting: string; model_id: string }>(
    "/calls/start",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_name,
        procedure,
        dia_postop,
        language: "es",
      }),
    },
  );
}

export function listDemoPatients() {
  return request<DemoPatient[]>("/demo/patients");
}

export function sendTurn(callId: string, message: string) {
  return request<AgentTurnResponse>(`/calls/${callId}/turn`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ call_id: callId, message }),
  });
}

export function endCall(callId: string, e2eLatencyMs: number[] = []) {
  return request<CallSummary>(`/calls/${callId}/end`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ e2e_latency_ms: e2eLatencyMs }),
  });
}

export function listDocuments() {
  return request<DocumentInfo[]>("/knowledge/documents");
}

export function uploadDocument(file: File, title: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  return request<DocumentInfo>("/knowledge/documents", {
    method: "POST",
    body: form,
  });
}

export function deleteDocument(docId: string) {
  return request<{ deleted: boolean }>(`/knowledge/documents/${docId}`, {
    method: "DELETE",
  });
}
