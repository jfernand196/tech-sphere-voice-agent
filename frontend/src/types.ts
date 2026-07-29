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
};

export type CallMessage = {
  role: string;
  content: string;
  sources?: SourceCitation[];
  escalate?: boolean;
  escalate_reason?: string | null;
  patient_state?: PatientState | null;
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
};

export type DocumentInfo = {
  doc_id: string;
  title: string;
  filename: string;
  chunk_count: number;
  created_at: string;
};
