# STATUS — Tech Sphere Voice Agent (handoff for humans & agents)

> **Read this file first** before changing code.  
> Last updated: 2026-07-29  
> Repo: https://github.com/jfernand196/tech-sphere-voice-agent  
> Default branch: `main`  
> Owner GitHub: `jfernand196`  
> Local path (original machine): `/Users/juan.buitrago/tech-sphere-voice-agent`

This document is the source of truth for **challenge context**, **what is built**, **what is missing**, **how to run**, and **how to continue work** on another machine or with another LLM/agent.

---

## 1. What this project is

Participation scaffold for **Tech Sphere Challenge 2026** (Colombia), organized by **Source Meridian** with communities (AI Thinkers Medellín, GDG, Databricks Community) and universities (Pascual Bravo, Universidad Nacional).

### Product goal

Build an **AI voice agent for post-operative follow-up**:

1. Patient leaves a procedure and needs monitoring in the first hours.
2. The agent “calls” the patient (browser voice/text — **no real telephony**).
3. Conversation adapts to answers.
4. Clinical answers are grounded in a **RAG knowledge base**.
5. Knowledge can be **hot-updated** (upload doc → agent learns; delete → agent forgets).
6. Every clinical answer must cite **which document** supported it.
7. Decision logic: **escalate to a human** or not.
8. On hang-up: **structured call summary**.

### Explicitly NOT required

- Real phone / Twilio telephony
- Real hospital system integrations (HL7/EHR)
- Enterprise auth / roles
- Coverage of all medical procedures (only the challenge dataset scenarios)

### Hard constraint (critical)

- **Orchestration / voice / RAG stack is free**
- **The LLM model is unique and mandatory for all teams** — announced with the technical sheet on **2026-08-07**
- Same model for everyone → win on engineering, not wallet (“no pay-to-win”)

---

## 2. Challenge calendar (official)

| Date | Event |
|---|---|
| 2026-07-22 | Live reveal + pre-registration opens |
| Until **2026-08-07** | Pre-registration |
| **2026-08-07 → 2026-08-10** | Build window (**3 days**). On Aug 7 teams receive: base GitHub repo (official), clinical dataset via **Delta Share (Databricks)**, tech sheet (mandatory model, gates, metrics) |
| 2026-08-10 → 2026-08-18 | Jury review → 3 finalists |
| **2026-09-05** | Awards + live demos (Universidad Nacional) |

Pre-register: https://sourcemeridian.com/tech-sphere-challenge

Note: Aug 7 may be a holiday in Colombia; the challenge still starts.

---

## 3. Evaluation (what graders care about)

### Eliminatory gates (must all pass or project is not scored)

1. Deliver all required deliverables
2. Solution can be started in **&lt; 15 minutes** (clean machine / good README)
3. Use the **mandatory model** from the Aug 7 sheet
4. Working **voice conversation** (browser OK)
5. Prove **hot knowledge update** (add/remove docs affects answers)

### Rubric themes (~100 points)

- RAG / clinical precision / live knowledge (~20)
- Decision making / escalate (~20)
- Problem understanding / conversation goal (~15)
- Voice UX / latency / naturalness
- Video pitch / argumentation
- Engineering hygiene / commit history (~15) — avoid one giant dump commit at the end

Also valued: compliance mindset (PHI/PII care even with synthetic data), metrics (P50/P95 latency, tokens, cost per call) in README.

### Prizes

USD $1000 in prepaid **Claude** accounts: $500 / $300 / $200.  
License for submitted code: **MIT** (code ownership remains with participant; organizers can clone/evaluate).

### Delivery expectations

Public GitHub repo with README + deps, architecture diagram, technical report (prompts, decisions, screenshots), demo video, MIT license.

---

## 4. Current implementation status

### Overall

**Working end-to-end MVP / scaffold** that already demonstrates the five product pillars with a **mock LLM** (no API key required). Architecture was refactored for clean code / SOLID evaluation. UI is clinical + responsive.

This repo is a **head start**. On Aug 7 it must absorb the **official** dataset + mandatory model + any starter repo rules from organizers.

### Done ✅

| Area | Status | Notes |
|---|---|---|
| FastAPI backend | Done | Port **8001** by default (`Makefile`) |
| React + Vite UI | Done | Proxy `/api` → `http://127.0.0.1:8001` |
| Call flow (text) | Done | start → turns → end summary |
| Browser STT/TTS | Done | Web Speech API; voice picker; stop on hang-up |
| RAG local | Done | Chunk + hash embeddings + JSON persistence |
| Hot knowledge console | Done | Upload `.txt/.md`, list, delete; agent retrieval updates |
| Source citations | Done | `sources[]` on each agent turn |
| Escalate logic | Done | Keyword safety + post-LLM guardrails (`safety.py`) |
| Structured summary | Done | JSON + human summary card in UI |
| Ports/adapters (SOLID) | Done | `LLMClient`, `KnowledgePort`, mock/Anthropic adapters |
| Unit tests (safety) | Done | `make test` → 3 tests |
| Clinical UI theme | Done | Medical blue/white; call phases setup/live/ended |
| Responsive mobile | Done | Portrait-oriented breakpoints, safe-areas, touch targets |
| MIT LICENSE | Done | |
| GitHub history | Done | Multiple commits + merged PRs (#1–#3) |
| Handoff docs | This file | `STATUS.md` + `ARCHITECTURE.md` + `README.md` |

### Partially done ⚠️

| Area | Gap |
|---|---|
| LLM | Anthropic client wired, but default is `LLM_PROVIDER=mock`. Mandatory model unknown until Aug 7 |
| RAG quality | Hash embeddings (not real embedding model); text files preferred; PDF not first-class |
| Voice quality | Browser TTS only; server STT/TTS stub exists but not implemented |
| Metrics | `latency_ms` per turn exists; **no** P50/P95 / tokens / cost reporting yet |
| Databricks Delta Share | Not integrated; uses local seed protocol |
| Official starter repo | Not merged; this is an independent scaffold |
| Deliverables pack | Missing formal architecture diagram image, technical report, demo video |
| Cold-start &lt;15 min | Documented; should be re-verified on a clean machine |
| Test coverage | Only safety tests; no RAG/call/API integration tests |
| KnowledgeConsole FE | Functional; less componentized than CallPanel |

### Not done ❌ (must do for challenge submission)

1. Wire **mandatory LLM** from Aug 7 tech sheet (`MODEL_ID` + provider + API key)
2. Connect **official clinical dataset** (Delta Share / Databricks)
3. Align with any **official base repository** rules if provided Aug 7
4. Report **metrics** in README: latency P50/P95, tokens, cost/call
5. Prove **&lt;15 min** setup on clean environment (record steps / video)
6. Produce **architecture diagram**, **technical report**, **demo video**
7. Harden RAG (real embeddings and/or pgvector/Chroma; PDF if dataset needs it)
8. Improve Spanish/Colombian colloquial robustness with real LLM prompts
9. Optional: server-side STT/TTS if browser UX/latency is insufficient
10. Keep **incremental commits** during the 3 build days (rubric)

---

## 5. Repository map

```text
tech-sphere-voice-agent/
├── STATUS.md                 ← YOU ARE HERE (agent handoff)
├── README.md                 ← how to run
├── ARCHITECTURE.md           ← SOLID / layers
├── LICENSE                   ← MIT
├── Makefile                  ← setup / backend / frontend / test
├── .env.example
├── samples/protocolo-herida.txt
├── backend/
│   ├── requirements.txt
│   ├── tests/test_safety.py
│   ├── data/                 ← runtime JSON/uploads (gitignored contents)
│   └── app/
│       ├── main.py           ← FastAPI app + seed protocol
│       ├── config.py         ← env settings (MODEL_ID, provider, ports)
│       ├── schemas.py        ← API / agent contracts
│       ├── ports.py          ← LLMClient, KnowledgePort Protocols
│       ├── api/              ← HTTP routers + deps composition root
│       ├── agent/            ← AgentService + LLM adapters + safety/parsing
│       ├── rag/              ← KnowledgeService + LocalVectorStore
│       ├── calls/            ← call history + summary
│       └── voice/            ← server STT/TTS seam (stub)
└── frontend/
    ├── package.json
    ├── vite.config.ts        ← proxy /api → :8001 (override VITE_API_TARGET)
    └── src/
        ├── App.tsx
        ├── api.ts
        ├── speech.ts         ← browser STT/TTS + stopSpeaking token
        ├── styles.css        ← clinical + responsive
        ├── hooks/            ← useCallSession, useAgentVoice
        └── components/       ← CallPanel, CallSummaryCard, KnowledgeConsole, ...
```

---

## 6. Runtime contracts (do not break casually)

### Agent turn response (backend → frontend)

Every turn should satisfy roughly:

```json
{
  "reply": "string spoken/shown to patient",
  "sources": [
    {"doc_id": "...", "title": "...", "chunk_id": "...", "excerpt": "..."}
  ],
  "patient_state": {
    "symptoms": ["..."],
    "severity": "none|mild|moderate|severe",
    "notes": "..."
  },
  "escalate": false,
  "escalate_reason": null,
  "model_id": "...",
  "latency_ms": 123
}
```

Defined in `backend/app/schemas.py` and mirrored in `frontend/src/types.ts`.

### Main HTTP API

- `GET /health`
- `POST /calls/start` `{ patient_name, procedure, language }`
- `POST /calls/{id}/turn` `{ call_id, message }`
- `POST /calls/{id}/end` → `CallSummary`
- `GET/POST/DELETE /knowledge/documents`
- `POST /knowledge/query`
- `GET /voice/capabilities`
- `POST /voice/transcribe` (stub)

Interactive docs: `http://127.0.0.1:8001/docs`

### Env (backend)

Copy `.env.example` → `backend/.env`:

```env
LLM_PROVIDER=mock                 # or anthropic when ready
MODEL_ID=claude-haiku-placeholder # replace Aug 7
ANTHROPIC_API_KEY=
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8001
CORS_ORIGINS=http://localhost:5173
```

LLM factory: `backend/app/agent/factory.py`  
If mandatory model is not Anthropic, add a new adapter implementing `LLMClient` — **do not** bloat `AgentService`.

---

## 7. How to run (any machine)

### Prerequisites

- Python 3.9+ (3.11+ recommended)
- Node.js 20+
- Chrome/Edge recommended for mic + TTS
- `gh` optional (already used for GitHub)

### Setup

```bash
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent
make setup
```

### Dev servers

```bash
# terminal 1
make backend    # http://127.0.0.1:8001

# terminal 2
make frontend   # http://127.0.0.1:5173
```

If backend port changes:

```bash
VITE_API_TARGET=http://127.0.0.1:PORT npm run dev
```

(from `frontend/`)

### Tests

```bash
make test
```

### Demo script (manual acceptance)

1. Open UI → tab **Llamada** → start call for a patient/procedure  
2. Say/type fever symptom → answer cites protocol sources  
3. Tab **Conocimiento** → upload `samples/protocolo-herida.txt` → ask about wound/pus → cites new doc  
4. Delete that doc → agent stops using it  
5. Say “no puedo respirar” → escalate badge/alert  
6. **Colgar** → speech stops immediately; summary card appears (JSON optional)  
7. Resize to phone width / device toolbar → layout still usable  

---

## 8. Architecture decisions (intentional)

1. **Text-first agent core** — voice is an adapter (browser today, server later).  
2. **Ports & adapters** — `AgentService` depends on `KnowledgePort` + `LLMClient`.  
3. **Safety is not only the LLM** — `safety.py` post-guards severe alarms.  
4. **Mock mode** — enables offline development before Aug 7 model announcement.  
5. **Local vector store** — simple, no Docker required for scaffold; replaceable.  
6. **Backend on 8001** — port 8000 often occupied by other local apps.  
7. **UI phases** — setup / live / ended to avoid confusing post-hangup states.  
8. **Clinical palette** — medical blue/white (not wellness mint).  
9. **Commit hygiene** — feature branches + PRs preferred over dumping to main.

See `ARCHITECTURE.md` for SOLID mapping.

---

## 9. Known bugs / fixed behaviors

| Issue | Resolution |
|---|---|
| UI showed `API: undefined` | Vite proxy was hitting wrong process on :8000; default target is :8001 |
| Hang-up kept speaking | `stopSpeaking()` token cancels multi-chunk TTS on hang-up / mute |
| Mock replies pasted raw RAG chunks | Mock composer paraphrases; sources stay in `sources[]` |
| Python 3.9 typing/`numpy` issues | Avoided modern-only syntax pitfalls; no numpy dependency |

---

## 10. Suggested work plan for another agent

### Before Aug 7 (safe prep)

1. Keep improving RAG retrieval quality without depending on official model.  
2. Add metrics collector scaffolding (latency list → P50/P95).  
3. Add more tests (RAG ingest/delete affects retrieve; escalate cases).  
4. Draft architecture diagram + report outline.  
5. Practice cold start from clean clone.  
6. Do **not** assume the final model id.

### On Aug 7 (challenge start)

1. Read official tech sheet + terms.  
2. Set `MODEL_ID` / provider / key.  
3. Integrate Delta Share dataset; replace seed docs as needed.  
4. Merge/rebase with official starter if required.  
5. Verify all 5 eliminatory gates.  
6. Record metrics + demo video.  
7. Commit often with small messages.

### Prompt for a new Cursor chat on another PC

```text
Read STATUS.md, README.md, and ARCHITECTURE.md in this repo.
Continue Tech Sphere 2026 post-op voice agent work.
Do not invent the mandatory LLM until the Aug 7 tech sheet is available.
Prefer ports/adapters; keep AgentService thin.
Current priority: <fill in: e.g. metrics / Delta Share / PDF RAG / tests>.
```

---

## 11. Git / PR history (context)

Merged PRs:

1. Clean architecture + SOLID-friendly structure  
2. Clinical UI polish (call states, summary card, knowledge UX)  
3. Mobile responsive layout  

Useful commit messages already on `main` include scaffold, backend, frontend, docs, TTS hang-up fix, UI polish, responsive.

Working branch convention used: `feature/<short-name>` → PR → merge to `main`.

---

## 12. Operator notes

- Participant profile (human): Full-stack engineer (Python/FastAPI, React, JS, PostgreSQL/Mongo, AWS; Databricks collaboration experience). Feels weaker on voice AI; scaffold intentionally maps voice to familiar web skills.  
- Challenge language: **Spanish (Colombia)** for the agent conversation.  
- Do not commit secrets (`.env`).  
- Runtime data under `backend/data/` is largely gitignored.  
- Frontend build: `cd frontend && npm run build`  
- Backend import path: run uvicorn with `PYTHONPATH=.` from `backend/` (Makefile does this).

---

## 13. Definition of “ready to submit”

- [ ] Mandatory model configured and used in running agent  
- [ ] Official dataset integrated  
- [ ] Gates 1–5 demonstrably pass  
- [ ] README includes setup &lt;15 min + metrics  
- [ ] Architecture diagram + technical report + demo video attached/linked  
- [ ] Public GitHub repo, MIT, clean commit history across build days  
- [ ] Hot knowledge add/delete proven in video  
- [ ] Escalate path proven in video  

Until those boxes are checked, treat this repo as **strong scaffold**, not final submission.
