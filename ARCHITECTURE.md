# Architecture — Tech Sphere Voice Agent

**Deliverable 02.** Architecture of the solution and the agent decision flow.  
Every box maps to code the jury can open (paths below).

Related: [`docs/informe-tecnico.md`](./docs/informe-tecnico.md) · [`STATUS.md`](./STATUS.md) · [`README.md`](./README.md)

---

## 1. System context

```mermaid
flowchart LR
  Paciente["Paciente / jurado<br/>Chrome · micrófono"]
  UI["React UI :5173<br/>CallPanel · KnowledgeConsole<br/>useCallSession · useAgentVoice"]
  API["FastAPI :8001<br/>calls · knowledge · health"]
  Agent["AgentService<br/>RAG → LLM → safety"]
  Groq["Groq Cloud<br/>Llama 3.3 70B"]
  Store["LocalVectorStore<br/>data/vector_store"]

  Paciente -->|voz / texto| UI
  UI -->|HTTP /api/*| API
  API --> Agent
  Agent -->|retrieve top_k=4| Store
  Agent -->|chat completions| Groq
  API -->|upload / delete| Store
  Agent -->|TTS texto| UI
  UI -->|Kokoro WAV / Web Speech fallback| Paciente
```

| Layer | Path |
|---|---|
| UI call + knowledge | `frontend/src/components/` |
| Voice STT/TTS | STT = browser Web Speech; TTS = browser (default) or server Kokoro/Piper via `TtsEnginePort` (`app/voice/base.py`) |
| HTTP adapters | `backend/app/api/` |
| Use-cases | `backend/app/agent/service.py`, `calls/service.py`, `rag/service.py` |
| Ports | `backend/app/ports.py` (`LLMClient`, `KnowledgePort`) |
| LLM adapters | `backend/app/agent/llm_groq.py`, `llm_gemini.py`, `llm_mock.py` |
| Factory | `backend/app/agent/factory.py` |
| Safety | `backend/app/agent/safety.py` |
| Prompts | `backend/app/agent/prompts.py` |
| RAG store | `backend/app/rag/store.py` (MiniLM 384-d cosine + BM25 → RRF; `EMBED_PROVIDER=hash` rollback) |

**Allowed LLM only:** Gemini Flash · Llama via Groq · local Llama/Phi. Anthropic is rejected in `factory.py`.

---

## 2. One turn (sequence)

```mermaid
sequenceDiagram
  participant FE as React UI
  participant API as FastAPI calls
  participant Ag as AgentService
  participant RAG as KnowledgeService
  participant LLM as GroqLLMClient
  participant Saf as safety.apply_safety_overrides

  FE->>API: POST /calls/{id}/turn {message}
  API->>Ag: respond(patient, history, message)
  Ag->>RAG: retrieve(message, top_k=4)
  RAG-->>Ag: chunks[]
  Ag->>LLM: complete(system, user_prompt)
  LLM-->>Ag: JSON draft (reply, sources, escalate, …)
  Ag->>Saf: apply_safety_overrides(message, draft)
  Note over Saf: Rules can FORCE escalate=true
  Saf-->>Ag: final AgentTurnResponse
  Ag-->>API: reply + sources + escalate + latency_ms
  API-->>FE: turn JSON
  FE->>FE: speakAgent(reply) via Web Speech TTS
```

Contract (`backend/app/schemas.py` → `AgentTurnResponse`):

`reply` · `sources[]` · `patient_state` · `escalate` · `escalate_reason` · `model_id` · `latency_ms`

---

## 3. Agent decision flow (escalate)

```mermaid
flowchart TD
  In["Mensaje del paciente"] --> RAG["RAG retrieve<br/>KnowledgeService"]
  RAG --> Prompt["build_user_prompt<br/>+ SYSTEM_PROMPT"]
  Prompt --> LLM["LLM JSON<br/>escalate draft"]
  LLM --> Guard{"safety.assess_message<br/>+ composites"}
  Guard -->|alarma / pide doctor| Force["escalate = true<br/>reason from rules<br/>severity ≥ severe/moderate"]
  Guard -->|sin alarma| Keep["Keep LLM escalate<br/>usually false"]
  Force --> Out["AgentTurnResponse"]
  Keep --> Out
  Out --> End{"CallService.end"}
  End -->|any escalate in call| Sum["CallSummary.escalate = true"]
```

**Order (important):**

1. LLM proposes `escalate` (prompt in `prompts.py`).
2. **Post-LLM guards are authoritative** — `apply_safety_overrides` in `safety.py` can force escalate even if the model said no.
3. There is **no** pre-LLM short-circuit on the Groq path; rules always run after the model.

Hard signals include: respiratory distress, heavy bleeding, high pain (8–10/10), high fever, purulent wound ± fever composites, explicit “quiero un doctor”.

Calibrated with `make eval-escalate` against kit verde/amarillo/rojo labels.

---

## 4. Hot knowledge (live console)

```mermaid
flowchart LR
  Upload["UI upload<br/>.txt / .md / .pdf"] --> Ingest["KnowledgeService.ingest"]
  Ingest --> Chunk["chunk + MiniLM embed<br/>LocalVectorStore"]
  Chunk --> Index[(vector_store)]
  Ask["Patient question"] --> Hybrid["hybrid search<br/>MiniLM cosine + BM25 → RRF"]
  Hybrid --> Index
  Delete["UI delete doc"] --> Drop["KnowledgeService.delete"]
  Drop --> Index
```

Embeddings: `backend/app/rag/embeddings.py` — default `fastembed` + `paraphrase-multilingual-MiniLM-L12-v2` (384-d, ONNX). Dim mismatch clears vectors and re-ingests from `metadata["path"]` on startup.

API: `POST /knowledge/documents` · `POST /knowledge/query` · `DELETE /knowledge/documents/{doc_id}`  
(`backend/app/api/knowledge.py`)

After delete, chunks are gone — the next turn cannot cite that document.

---

## 5. Ports / adapters (SOLID)

```text
UI (React)
        │ /api/*
        ▼
API routers                 ← inbound adapters
        ▼
Use-cases                   ← AgentService, CallService, KnowledgeService
        │ depends on ports
        ▼
Ports (Protocol)            ← LLMClient, KnowledgePort
        ▼
Adapters                    ← Groq / Gemini / Mock · LocalVectorStore
```

| Principle | Where |
|---|---|
| SRP | `safety.py` vs `llm_*` vs `parsing` |
| OCP | New LLM = subclass `PromptedLLMClient` + `factory.py` branch |
| LSP | Mock / Groq / Gemini all satisfy `LLMClient` |
| ISP | Small ports only |
| DIP | `AgentService` depends on Protocols; wiring in `api/deps.py` |

---

## 6. Runtime configuration

From `backend/.env` (see `.env.example`):

| Key | Role |
|---|---|
| `LLM_PROVIDER` | `groq` (default for demo) · `gemini` · `mock` |
| `MODEL_ID` | e.g. `llama-3.3-70b-versatile` |
| `GROQ_API_KEY` / `GEMINI_API_KEY` | Cloud credentials |
| `EMBED_PROVIDER` | `fastembed` (default) · `hash` (offline rollback) |
| `TTS_PROVIDER` | `auto` (Kokoro if models present) · `kokoro` · `browser` |
| `KOKORO_VOICE` | e.g. `ef_dora` (Spanish) |
| `CORS_ORIGINS` | UI origin |
| `DATA_DIR` | Uploads + vector store + calls JSON |

---

## 7. Conversation design (what the jury hears)

Soft agenda lives in `backend/app/agent/prompts.py` (not a hard clinical state machine):

```mermaid
flowchart TD
  Open["Apertura<br/>greeting en calls.py"] --> Explore["Exploración<br/>síntomas / herida / fiebre"]
  Explore --> Orient["Orientación<br/>1 indicación RAG por turno"]
  Orient --> Explore
  Explore --> Amb{"¿Ambiguo?"}
  Amb -->|sí| Ask["Indaga 1 detalle"]
  Ask --> Explore
  Amb -->|alarma| Esc["safety → escalate"]
  Explore --> Close["Cierre<br/>paciente se despide → 1 paso + listo para colgar"]
  Explore --> Off{"¿Fuera de guion?"}
  Off -->|ajeno / inyección| Redir["Redirige a recuperación"]
  Redir --> Explore
```

| Rubric ask | Implementation |
|---|---|
| Open / conduct / close | Template greeting → prompt agenda → user hang-up + `CallSummary` |
| Off-script | Prompt redirect + ignore role-change; escalate keywords for “quiero un doctor” |
| Long instructions | One care step per turn; ask before the next |
| Silences | UI `CallStatusBanner` (thinking / listening); barge-in stops TTS |

**Covered vs challenge:** voice call, RAG+citations, hot knowledge, escalate, summary, metrics.  
**Intentional gaps:** no telephony/HIS; no hard stage automaton; STT quality = browser.

---

## 8. What is intentionally out of scope

- Real telephony / hospital HIS
- Enterprise auth / roles
- Server-side STT (browser Web Speech; Kokoro covers TTS only)
- External vector DB (local MiniLM via fastembed; Chroma/BGE-M3 left as future work)
