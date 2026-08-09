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
| Python | **3.9+** | `python3 --version` |
| Node.js | **18+** (LTS ok) | `node -v` |
| npm | comes with Node | `npm -v` |
| Chrome or Edge | recent | needed for Web Speech (mic + TTS) |

**API key (free):** create a Groq key at https://console.groq.com/keys  
Keep the key ready to paste. No paid plan required.

### Timed path — copy/paste

```bash
# 1) Clone
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent

# 2) Install deps + create backend/.env from the example (~1–3 min)
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
| Mic / speech errors in the UI | Use Chrome/Edge; allow microphone; HTTPS not required on localhost. |
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

## Metrics (observed)

Measured on a cold machine path: agent turn = time from request accepted until JSON reply ready (`latency_ms` in each turn). Browser STT/TTS adds extra wall time on top (not included below).

| Metric | Value | How |
|---|---|---|
| Agent-turn latency P50 | **~1.5 s** | Groq `llama-3.3-70b-versatile`, 10 kit escalate turns (`make eval-escalate`) |
| Agent-turn latency P95 | **~2.2 s** | Same sample |
| Model invocations / turn | **1** | One chat completion per patient utterance |
| RAG queries / turn | **1** | Local retrieve before the LLM call |
| Tokens in / out per turn | *see live turn logs* | Groq usage not yet rolled up in README; each API response exposes usage — capture during jury session from network/logs |
| Est. cost / call (≈6 turns) | **~$0.00–0.01** | Groq free tier for challenge; production list prices for Llama 3.3 70B on Groq are typically well under a cent for short Spanish turns |

Voice path note: end-to-end “patient stops speaking → agent audio starts” ≈ STT finalize + agent turn + TTS start. On localhost Chrome this is usually a few seconds total when the model is warm.

Do not treat these numbers as synthetic benchmarks — re-check `latency_ms` on the Call tab during the live session.

---

## What is included

| Module | Role |
|---|---|
| RAG | Upload `.txt/.md/.pdf`, list, delete; local retrieval + citations |
| Agent | Orchestration + safety + JSON contract |
| Calls | History + hang-up summary |
| Voice | Browser Web Speech (STT/TTS) |
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
