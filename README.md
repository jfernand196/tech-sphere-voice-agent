# Tech Sphere 2026 — Post-operative voice agent

Browser voice agent for Colombian post-op follow-up: clinical RAG, hot knowledge console, source citations, escalate-to-human, and structured call summary.

| | |
|---|---|
| Public repo | https://github.com/jfernand196/tech-sphere-voice-agent |
| Allowed LLM (default) | **Groq + Llama** `llama-3.3-70b-versatile` |
| UI | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8001 |

> Challenge mirrors (Spanish): [`docs/challenge/`](./docs/challenge/). Handoff for builders: [`STATUS.md`](./STATUS.md).

---

## Cold start (≤ 15 minutes)

This is the **only** path the jury needs. Follow it top to bottom. Optional kit / eval steps are **below** and do **not** count toward lift.

### Before the clock (2–3 min)

Install once on the machine (not part of the app install itself, but required):

| Tool | Suggested version | Check |
|---|---|---|
| macOS or Linux | — | — |
| Git | any recent | `git --version` |
| Make | any | `make --version` |
| Python | **3.12 recommended** (3.10+ for Kokoro TTS; 3.9 works only with browser TTS) | `python3.12 --version` |
| Node.js | **18+** (LTS ok) | `node -v` |
| npm | comes with Node | `npm -v` |
| Chrome or Edge | recent | needed for Web Speech STT (mic); TTS uses Kokoro when warmed |

**API key (free):** create a Groq key at https://console.groq.com/keys  
Keep the key ready to paste. No paid plan required.

### Timed path — copy/paste

```bash
# 1) Clone
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent

# 2) Install deps + create backend/.env from the example (~3–8 min)
#    Prefers python3.12. Also pre-downloads:
#      - MiniLM embeddings (~220 MB) via `make warm-embed`
#      - Kokoro TTS int8 (~115 MB) via `make warm-kokoro`
#      - Piper Spanish voices (~120 MB) via `make warm-piper`
#    so the first API boot does not pay those downloads on the clock.
make setup

# 3) Paste your Groq key into backend/.env
#    Open the file and set:
#      LLM_PROVIDER=groq
#      MODEL_ID=llama-3.3-70b-versatile
#      GROQ_API_KEY=gsk_...your_key...
#    Leave other lines as-is.

# 4) Prove the LLM answers (must print OK)
make smoke-groq

# 5) Start API (terminal 1) — leave it running
make backend
#    Expect: Uvicorn on http://127.0.0.1:8001

# 6) Start UI (terminal 2) — leave it running
make frontend
#    Expect: Vite on http://127.0.0.1:5173
```

### Done criteria (stop the clock when all are true)

In a **third** terminal (or browser):

```bash
make verify
```

You should see `status=ok`, `llm_ready=true`, `llm_provider=groq`.

Then open **http://127.0.0.1:5173** — the Call tab and Knowledge console load.  
That is “solution up and accessible.” Demo exercises (voice, upload, escalate) are **after** lift; they are not part of the 15-minute clock.

### If something fails

| Symptom | Fix |
|---|---|
| `make smoke-groq` → missing key | Set `GROQ_API_KEY` in `backend/.env` (no quotes). Re-run smoke. |
| `llm_ready=false` / `degraded` | Key wrong or provider not `groq`. Fix `.env`, restart `make backend`. |
| Port 8001 or 5173 busy | Stop the other process, or set `BACKEND_PORT` / Vite port and keep UI proxy aligned. |
| `python3` / `npm` not found | Install Python 3.9+ and Node 18+; re-run `make setup`. |
| First RAG slow / model download | Run `make warm-embed` (also part of `make setup`). Offline rollback: `EMBED_PROVIDER=hash` in `backend/.env`. |
| Robot / OS-dependent TTS | UI default is **Web Speech** (fast). Kokoro/Piper appear after `make warm-kokoro` / `make warm-piper` (`TTS_PROVIDER=auto`). |
| Mic / speech errors in the UI | Use Chrome/Edge; allow microphone; HTTPS not required on localhost. |
| `kokoro-onnx` install fails on 3.9 | Recreate venv with Python 3.12: `rm -rf backend/.venv && make setup`. |
| Groq HTTP 429 | Free-tier rate limit — wait ~30s and retry the turn. |

Without a key, the backend **does not** silently fall back to `mock` when `LLM_PROVIDER=groq`.

---

## Allowed language models (hard constraint)

Orchestration, voice, and RAG are open. **The LLM is not:**

| Allowed | Not allowed |
|---|---|
| Gemini Flash (AI Studio) | Claude / Anthropic |
| Llama via Groq | Paid GPT / other families |
| Local Llama 3.x 1B–3B or Phi Mini (Ollama) | |

Default in this repo: **Groq + Llama** (low latency for voice). Alternative: set `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` (see `.env.example`). Details: [`docs/challenge/stack-tecnico.md`](./docs/challenge/stack-tecnico.md).

---

## After lift — 2-minute smoke demo

1. **Call** tab → pick a demo patient (e.g. day 7 · rojo) or edit a free patient.  
2. Speak or type a symptom from the on-screen hint (hint is actor-only; not sent to the model).  
3. Ask a clinical care question → reply should include `sources`.  
4. **Knowledge** tab → upload a small `.txt` / `.pdf` → ask about it → delete → agent stops using it.  
5. Say “no puedo respirar” or “quiero un doctor” → escalate.  
6. **End call** → structured summary card.

Seed protocol is loaded automatically on backend start (enough for lift + basic RAG). Official clinical PDFs are optional (next section).

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

## Metrics (challenge §5)

Instrumentado en código. Tras una llamada de voz, el **resumen al colgar** muestra totales y P50/P95; cada burbuja del agente muestra `e2e` / `api` / `tok`.

### How we measure

| Metric | Definition in this repo |
|---|---|
| **E2E latency** (official) | `performance.now()` when Web Speech STT returns the final transcript → TTS `utterance.onstart` (agent audio begins) |
| **Agent latency** (server) | Backend `latency_ms`: RAG retrieve + LLM + safety |
| **Tokens** | Groq `usage.prompt_tokens` / `completion_tokens` (Gemini: `usageMetadata`) |
| **Invocations / RAG** | **1** model call and **1** retrieve per patient turn |
| **Cost** | `(tokens_in/1e6)*$0.59 + (tokens_out/1e6)*$0.79` list price for Llama 3.3 70B on Groq; free tier ≈ $0 at runtime |

### How to refresh numbers

1. `make backend` + `make frontend` with Groq key  
2. Call tab → **Hablar** for ≥10 voice turns (mic on, voice out on)  
3. End call → read P50/P95 e2e + token totals on the summary card (also in JSON)  
4. Paste into the table below

### Observed sample (voice call, 10 mic turns)

Groq `llama-3.3-70b-versatile` · Web Speech STT + Web Speech TTS · caso día 7 crítico · resumen al colgar.

| Metric | Value | Notes |
|---|---|---|
| E2E voice latency P50 | **1136 ms** | STT final → TTS audio start |
| E2E voice latency P95 | **1427 ms** | Same call |
| Agent-turn latency P50 | **1044 ms** | Backend RAG + LLM + safety (`api`) |
| Agent-turn latency P95 | **1337 ms** | Same call |
| Model invocations / turn | **1** | 10 inv / 10 turns |
| RAG queries / turn | **1** | 10 RAG / 10 turns |
| Tokens in / out | **8422 / 2208** | Call totals (Groq usage) |
| Est. cost / call | **$0.0067 USD** | Prod list-price estimate; free tier ≈ $0 at runtime |

Offline kit check (`make eval-escalate`) previously showed agent-turn ~1.5 s / ~2.2 s P50/P95 on 10 text cases — use the voice hang-up card for the official E2E numbers above.

---

## What is included

| Module | Role |
|---|---|
| RAG | Upload `.txt/.md/.pdf`, list, delete; local retrieval + citations |
| Agent | Orchestration + safety + JSON contract |
| Calls | History + hang-up summary |
| Voice | Browser Web Speech STT + TTS selector: **Web Speech (default)** · Kokoro · Piper |
| UI | Knowledge console + call interface |

Adapters: `backend/app/agent/llm_groq.py`, `llm_gemini.py`. Factory: `factory.py`.

## Tests

```bash
make test
```

## Submission deliverables

| # | Deliverable | Where |
|---|---|---|
| 01 | Public repo + cold-start README | this file |
| 02 | Architecture + decision-flow diagram | [`ARCHITECTURE.md`](./ARCHITECTURE.md) |
| 03 | Technical report (model + why, prompts) | [`docs/informe-tecnico.md`](./docs/informe-tecnico.md) |
| 04 | Demo video + 2 on-camera answers | record with [`docs/guion-video.md`](./docs/guion-video.md) |

Must prove in session/video: ≤15 min lift, allowed LLM, realtime voice, upload/delete knowledge.  
Scoring: [`docs/challenge/rubrica-evaluacion.md`](./docs/challenge/rubrica-evaluacion.md).
