# Tech Sphere 2026 — Post-operative voice agent

**Para el jurado (ES):** agente de voz de seguimiento post-operatorio (Colombia). Se levanta en **≤15 minutos** solo con esta sección *Cold start*. El modelo permitido por defecto es **Groq + Llama**. La demo de micrófono, subir/borrar conocimiento y escalate es **después** del reloj.

Browser voice agent for Colombian post-op follow-up: clinical RAG, hot knowledge console, source citations, escalate-to-human, and structured call summary.

| Item | Value |
|------|-------|
| Public repo | https://github.com/jfernand196/tech-sphere-voice-agent |
| Allowed LLM (default) | **Groq + Llama** `llama-3.3-70b-versatile` |
| UI | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8001 |

> Reto / rúbrica (español): [`docs/challenge/`](./docs/challenge/). Informe técnico: [`docs/informe-tecnico.md`](./docs/informe-tecnico.md).

---

## Cold start (≤ 15 minutes) — jury path

This is the **only** path needed to stop the G2 clock. Follow it top to bottom.

- **Counts toward 15 min:** clone → `make setup` → key → smoke → backend + frontend → `make verify` → UI loads.
- **Does not count:** voice demo, upload/delete knowledge, escalate, official kit, eval scripts, metrics refresh.

### Before the clock (2–3 min)

Install once on the machine (tools only — not the app):

| Tool | Suggested version | Check |
|---|---|---|
| macOS or Linux | — | — |
| Git | any recent | `git --version` |
| Make | any | `make --version` |
| Python | **3.12 recommended** (3.10+ OK) | `python3.12 --version` |
| Node.js | **18+** (LTS ok) | `node -v` |
| npm | comes with Node | `npm -v` |
| Chrome or Edge | recent | mic / Web Speech STT |

**API key (free):** https://console.groq.com/keys — keep it ready to paste. No paid plan required.

### Timed path — copy/paste

```bash
# 1) Clone
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent

# 2) Install deps + create backend/.env (~3–8 min on a normal network)
#    Prefers python3.12. Pre-downloads embeddings (+ optional local TTS voices)
#    so the first API boot does not pay those downloads later.
make setup

# 3) Paste your Groq key into backend/.env
#      LLM_PROVIDER=groq
#      MODEL_ID=llama-3.3-70b-versatile
#      GROQ_API_KEY=gsk_...your_key...
#    Leave other lines as-is.

# 4) Prove the LLM answers (must print OK)
make smoke-groq

# 5) Start API (terminal 1) — leave it running
make backend
#    Expect: Uvicorn on http://127.0.0.1:8001
#    Expect log: [rag] index ready: docs=… chunks=…

# 6) Start UI (terminal 2) — leave it running
make frontend
#    Expect: Vite on http://127.0.0.1:5173
```

### Done criteria — **stop the clock** when all are true

In a **third** terminal:

```bash
make verify
```

You should see something like:

```text
status=ok llm_ready=true rag_ok=true docs=… chunks=… llm=groq/llama-3.3-70b-versatile
```

Then open **http://127.0.0.1:5173** — Call tab and Knowledge console load.

That is “solution up and accessible” for G2.  
**Do not** spend clock time on mic tests, uploads, or escalate — those are the smoke demo **after** lift.

### If something fails

| Symptom | Fix |
|---|---|
| `make smoke-groq` → missing key | Set `GROQ_API_KEY` in `backend/.env` (no quotes). Re-run smoke. |
| `llm_ready=false` | Key wrong or `LLM_PROVIDER` not `groq`. Fix `.env`, restart `make backend`. |
| `rag_ok=false` / `degraded` with docs but 0 chunks | Restart `make backend` and wait for `[rag] index ready` / re-embed log. |
| Port 8001 or 5173 busy | Stop the other process (`make frontend` uses `:5173` strict). |
| `python3` / `npm` not found | Install Python 3.12 + Node 18+; re-run `make setup`. |
| First RAG / model download slow | Already covered by `make setup` (`warm-embed`). Offline rollback: `EMBED_PROVIDER=hash`. |
| Mic / speech errors | Chrome/Edge; allow microphone; localhost is fine (no HTTPS). |
| `kokoro-onnx` fails on Python 3.9 | Use 3.12: `rm -rf backend/.venv && make setup`. TTS default in UI is **Web Speech** anyway. |
| Groq HTTP 429 | Free-tier limit — wait ~30s and retry. |

Without a key, the backend **does not** silently fall back to `mock` when `LLM_PROVIDER=groq`.

---

## Allowed language models (hard constraint — G3)

Orchestration, voice, and RAG are open. **The LLM is not:**

| Allowed | Not allowed |
|---|---|
| Gemini Flash (AI Studio) | Claude / Anthropic |
| Llama via Groq | Paid GPT / other families |
| Local Llama 3.x 1B–3B or Phi Mini (Ollama) | |

Default in this repo: **Groq + Llama**. Alternative: `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` (see `.env.example`). Details: [`docs/challenge/stack-tecnico.md`](./docs/challenge/stack-tecnico.md).

---

## After lift — 2-minute smoke demo (not on the 15‑min clock)

Use this **after** `make verify` succeeds and the UI is open:

1. **Call** → pick a demo patient (e.g. day 7 · crítico) or edit a free patient.  
2. Speak or type a symptom from the on-screen hint (hint is actor-only; not sent to the model).  
3. Ask a clinical care question → reply should show **sources**.  
4. **Knowledge** → upload a small `.txt` / `.pdf` → ask about it → **Eliminar** → agent stops using it.  
5. Say “no puedo respirar” or “quiero un doctor” → **escalate**.  
6. **End call** → structured summary card (latency / tokens).

Voice TTS defaults to **Web Speech** (fast). Kokoro / Piper are optional local engines after `make warm-kokoro` / `make warm-piper`.

Seed protocol loads automatically on backend start (enough for lift + basic RAG). Official clinical PDFs are optional (next section).

---

## Optional — official kit (not required for cold start)

```bash
make kit-clone                                          # ~127MB, gitignored
make ingest-kit ARGS='--scenario cholecystitis --limit 8'
make export-demo                                        # refresh UI patient catalog
make eval-escalate ARGS='--provider mock'               # offline escalate score
make eval-escalate                                      # same with .env LLM (Groq)
```

Escalate target: **all rojo cases escalate**; keep verde false positives low.  
Results: `samples/eval_escalate_results.json` (gitignored).

---

## Metrics (challenge §5) — after lift

Instrumented in code. Numbers below are from a sample voice call; refresh with a live hang-up card (not part of cold start).

| Metric | Definition in this repo |
|---|---|
| **E2E latency** (official) | STT final transcript → TTS audio start (`performance.now`) |
| **Agent latency** (server) | Backend `latency_ms`: RAG + LLM + safety |
| **Tokens** | Groq `usage` (or Gemini `usageMetadata`) |
| **Invocations / RAG** | **1** model call and **1** retrieve per patient turn |
| **Cost** | Groq Llama 3.3 70B list-price estimate; free tier ≈ $0 at runtime |

### Observed sample (10 mic turns)

Groq `llama-3.3-70b-versatile` · Web Speech STT + TTS · caso día 7 crítico.

| Metric | Value |
|---|---|
| E2E P50 / P95 | **1136 / 1427 ms** |
| Agent-turn P50 / P95 | **1044 / 1337 ms** |
| Invocations / RAG per turn | **1 / 1** |
| Tokens in / out | **8422 / 2208** |
| Est. cost / call | **$0.0067 USD** |

How to refresh: run a ≥10-turn voice call → End call → read P50/P95 on the summary card. More detail: [`docs/informe-tecnico.md`](./docs/informe-tecnico.md).

---

## What is included

| Module | Role |
|---|---|
| RAG | Upload `.txt/.md/.pdf`, list, delete; local retrieval + citations |
| Agent | Orchestration + safety + JSON contract |
| Calls | History + hang-up summary |
| Voice | Web Speech STT + TTS (Web Speech default; Kokoro / Piper optional) |
| UI | Knowledge console + call interface |

## Tests

```bash
make test          # unit / API tests
make smoke-app     # live smoke (backend must be running)
make rehearse-jury # RAG · OOD · G5 · escalate · injection (backend up)
```

## Submission deliverables

| # | Deliverable | Link |
|---|---|---|
| 01 | Public repo + cold-start README | https://github.com/jfernand196/tech-sphere-voice-agent |
| 02 | Architecture + decision-flow diagram | https://github.com/jfernand196/tech-sphere-voice-agent/blob/main/ARCHITECTURE.md |
| 03 | Technical report (model + why, prompts) | https://github.com/jfernand196/tech-sphere-voice-agent/blob/main/docs/informe-tecnico.md |
| 04 | Demo video + 2 on-camera answers | https://drive.google.com/file/d/1rjx0qMlYmtqqT44bNZotweVjgCvfxkXE/view?usp=sharing |

Local copies: [`ARCHITECTURE.md`](./ARCHITECTURE.md) · [`docs/informe-tecnico.md`](./docs/informe-tecnico.md).

Must prove in session/video: ≤15 min lift, allowed LLM, realtime voice, upload/delete knowledge.  
Scoring: [`docs/challenge/rubrica-evaluacion.md`](./docs/challenge/rubrica-evaluacion.md).
