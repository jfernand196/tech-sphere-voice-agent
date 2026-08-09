export type SourceCitation = {
  doc_id: string;
  title: string;
  chunk_id: string;
  excerpt?: string | null;
};

export type PatientState = {
  symptoms: string[];
  severity: "none" | "mild" | "moderate" | "severe";
  notes?: string | null;
};

export type AgentTurnResponse = {
  reply: string;
  sources: SourceCitation[];
  patient_state: PatientState;
  escalate: boolean;
  escalate_reason?: string | null;
  model_id?: string | null;
  latency_ms?: number | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
  model_invocations?: number | null;
  rag_queries?: number | null;
};

export type CallMessage = {
  role: string;
  content: string;
  sources?: SourceCitation[];
  escalate?: boolean;
  escalate_reason?: string | null;
  patient_state?: PatientState | null;
};

/** Chat bubble model used by the call UI (API message + optional latency). */
export type ChatItem = CallMessage & {
  latency_ms?: number | null;
  e2e_latency_ms?: number | null;
  tokens_in?: number | null;
  tokens_out?: number | null;
};

export type CallSummary = {
  call_id: string;
  patient_name: string;
  procedure: string;
  symptoms: string[];
  severity: string;
  escalate: boolean;
  escalate_reason?: string | null;
  sources_used: SourceCitation[];
  summary_text: string;
  turn_count: number;
  tokens_in_total?: number;
  tokens_out_total?: number;
  model_invocations_total?: number;
  rag_queries_total?: number;
  agent_latency_p50_ms?: number | null;
  agent_latency_p95_ms?: number | null;
  e2e_latency_p50_ms?: number | null;
  e2e_latency_p95_ms?: number | null;
  cost_usd_estimate?: number | null;
  cost_note?: string | null;
};

export type DocumentInfo = {
  doc_id: string;
  title: string;
  filename: string;
  chunk_count: number;
  created_at: string;
  metadata?: Record<string, unknown>;
};

export type DemoPatient = {
  id: string;
  paciente_id: string;
  nombre: string;
  procedimiento: string;
  dia_postop: number;
  label: string;
  demo_hint: string;
  ciudad?: string;
  eps?: string;
};
