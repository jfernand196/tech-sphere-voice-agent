# Tech Sphere 2026 — Post-operative voice agent

AI voice agent for post-operative follow-up: browser conversation, clinical RAG, hot knowledge console, source citations, escalate-to-human, and structured call summary.

> **Handoff:** start with [`STATUS.md`](./STATUS.md).  
> **Official rules (Spanish mirrors):** [`docs/challenge/`](./docs/challenge/). Full kit: [TechSphere2026/ParticipantArtifacts](https://github.com/TechSphere2026/ParticipantArtifacts).

## Allowed language models (hard constraint)

Orchestration, voice, and RAG are open choices. **The LLM is not:**

| Allowed (free / local) | Not allowed |
|---|---|
| Gemini Flash (AI Studio) | Claude / Anthropic |
| Llama via Groq | Paid GPT / other families |
| Local Llama 3.x 1B–3B or Phi Mini (Ollama) | |

Using a model outside that list **disqualifies** the submission. Details: [`docs/challenge/stack-tecnico.md`](./docs/challenge/stack-tecnico.md).

This repo defaults to **Groq + Llama** (low latency for voice). Alternative: **Gemini Flash** (long context).

## Step 1 — Enable Groq

1. Create a free API key at https://console.groq.com/keys  
2. In `backend/.env` (defaults to `LLM_PROVIDER=groq`):

```env
LLM_PROVIDER=groq
MODEL_ID=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_your_key_here
```

3. Verify the model responds:

```bash
make smoke-groq
```

You should see `OK — Groq respondió.` If it says the key is missing, paste it and retry.  
4. Restart the backend. `GET /health` should show `"llm_ready": true` and `"llm_provider": "groq"`.

Without a key, the backend **does not** silently fall back to `mock` when `LLM_PROVIDER=groq`.

## Quick start (< 15 min)

```bash
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent
make setup
# edit backend/.env → GROQ_API_KEY=...
make smoke-groq

# Official kit (~127MB, gitignored) — dataset + clinical PDFs
make kit-clone

# terminal 1
make backend    # http://127.0.0.1:8001

# terminal 2
make frontend   # http://127.0.0.1:5173
```

Optional — index clinical PDFs into the local RAG store:

```bash
make ingest-kit ARGS='--scenario cholecystitis --limit 8'
```

Adapters: `backend/app/agent/llm_groq.py`, `llm_gemini.py`. Factory: `factory.py`.

## What is included

| Module | Role |
|---|---|
| RAG | Upload `.txt/.md/.pdf`, list, delete; local retrieval |
| Agent | Orchestration + safety + JSON contract |
| Calls | History + hang-up summary |
| Voice | Browser Web Speech (STT/TTS) |
| UI | Knowledge console + call interface |

## Demo checklist

1. **Voice** → Call tab → speak / listen.  
2. **RAG** → clinical question; reply includes `sources`.  
3. **Live knowledge** → upload PDF/txt → ask again → delete → agent stops using it.  
4. **Escalate** → “no puedo respirar” / “quiero un doctor”.  
5. **Summary** → End call → JSON + summary card.

## Tests

```bash
make test
```

## Submission requirements

Must ship: public repo, architecture diagram, technical report, demo video.  
Must prove: setup in ≤15 minutes, allowed LLM, realtime voice, upload/delete knowledge from the console.  
Scoring details: [`docs/challenge/rubrica-evaluacion.md`](./docs/challenge/rubrica-evaluacion.md).
