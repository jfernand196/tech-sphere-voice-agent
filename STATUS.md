# STATUS — Tech Sphere Voice Agent (handoff for humans & agents)

> **Read this file first** before changing code.  
> Last updated: **2026-08-08** (UI locale ES/EN; agent language stays Spanish)  
> Repo: https://github.com/jfernand196/tech-sphere-voice-agent  
> Default branch: `main`  
> Owner GitHub: `jfernand196`  
> Local path: `/Users/juan.buitrago/tech-sphere-voice-agent`  
> Official kit: https://github.com/TechSphere2026/ParticipantArtifacts → `make kit-clone` → `./official-kit/`

This document is the source of truth for **challenge context**, **what is built**, **what is missing**, **how to run**, and **how to continue work**.

---

## 1. What this project is

Participation implementation for **Tech Sphere Challenge 2026** (Source Meridian): AI **voice** agent for Colombian post-operative follow-up.

### Product goal

1. Browser voice/text “call” (no real telephony).
2. Adaptive conversation in Spanish (Colombia).
3. Clinical answers grounded in **RAG** (official `dataset/textos/` PDFs + hot uploads).
4. Hot knowledge console: upload → learn; delete → forget.
5. Cite which document supported each clinical answer.
6. Escalate-to-human decision (false negatives weigh more).
7. Structured call summary on hang-up.

### Hard constraint (CRITICAL — updated 2026-08-08)

- Orchestration / voice / RAG / embeddings: **open**.
- **LLM must be one of the allowed families** ([`docs/challenge/stack-tecnico.md`](./docs/challenge/stack-tecnico.md)):
  - Google **Gemini Flash** (free AI Studio)
  - Meta **Llama** via **Groq** (free)
  - Meta **Llama 3.x** 1B–3B **local** (Ollama)
  - Microsoft **Phi Mini** 3.5+ **local**
- Using **Anthropic/Claude or any other family disqualifies** the submission (eliminatory model check).
- Free/local models are preferred so the jury scores engineering, not paid model quality.

### Official data (`make kit-clone`)

| Path | Content |
|---|---|
| `official-kit/dataset/dataset_final.xlsx` | 3991 turns, 40 patients, 160 cases, labels verde/amarillo/rojo |
| `official-kit/dataset/trayectorias_postop_silver.xlsx` | Clinical ground truth per call |
| `official-kit/dataset/perfiles_clinicos_*.xlsx` | Procedure, age, comorbidities |
| `official-kit/dataset/perfiles_pacientes_co.xlsx` | Colombian demographics |
| `official-kit/dataset/textos/` | **107 clinical PDFs** (5 scenarios) — RAG fuel |

Join: `caso_id = "caso_" + trayectoria_id`. Filter by `capa` (`capa1_limpia` / `capa2_ruidosa`).

---

## 2. Challenge calendar

| Date | Event |
|---|---|
| **2026-08-07 → 2026-08-10** | **Build + submit window** |
| 2026-08-10 → 2026-08-18 | Jury → 3 finalists |
| **2026-09-05** | Awards + live demos |

Pre-register / portal: https://sourcemeridian.com/tech-sphere-challenge

---

## 3. Evaluation

Mirrors: [`docs/challenge/rubrica-evaluacion.md`](./docs/challenge/rubrica-evaluacion.md).

### Eliminatory checks (binary — official rubric uses numbered labels; this handoff uses plain English)

| Check | Requirement |
|---|---|
| Deliverables | Public repo, architecture diagram, technical report, demo video (+ 2 on-camera questions) |
| Cold start | Liftable in **≤15 min** from README alone (credentials documented) |
| Allowed LLM | **Allowed LLM family only** + declare model and rationale in the report |
| Voice | Realtime **voice** works (user speaks + agent speaks back) |
| Live knowledge | Hot knowledge from **admin console** (upload is used; delete is forgotten) |

### Scoring (100 pts)

| Pts | Criterion |
|---:|---|
| 20 | RAG, clinical precision, live knowledge |
| 20 | Decision / escalate logic |
| 15 | Problem understanding / conversation design |
| 15 | Voice conversation quality |
| 15 | Video pitch + demo |
| 15 | Repo, process, practices |

Asymmetry: **missing an escalate when needed is catastrophic** vs false positive.

---

## 4. Current implementation status

### Overall

Working end-to-end MVP. **Groq (Llama) and Gemini Flash adapters** are wired (Groq verified via `make smoke-groq`). Official kit can be cloned and PDF-ingested. Anthropic is **blocked** in the factory so an allowed LLM is always used.

### Done ✅

| Area | Notes |
|---|---|
| FastAPI + React UI | API `:8001`, UI `:5173` |
| Call flow + browser STT/TTS | Phases setup/live/ended; stop TTS on hang-up |
| RAG local + hot console | `.txt/.md/.pdf` upload; list; delete; citations |
| Escalate + summary | Keyword safety + post-LLM guards |
| SOLID ports | `LLMClient`, `KnowledgePort`; mock / groq / gemini |
| Official kit docs in repo | `docs/challenge/*` |
| Kit clone + ingest script | `make kit-clone`, `make ingest-kit` |
| Escalate eval | `make eval-escalate` vs kit labels |
| Cold-start README | Timed path + `make verify` done criteria |
| Diagram + informe | `ARCHITECTURE.md` + `docs/informe-tecnico.md` |
| MIT + GitHub history | Incremental PRs on `main` |

### Partially done ⚠️

| Area | Gap |
|---|---|
| LLM in demo | **Groq OK** (`make smoke-groq` pasó con `llama-3.3-70b-versatile`) |
| RAG quality | **17 cholecystitis PDFs ingested**; **hybrid BM25 + MiniLM 384-d (fastembed) → RRF**; not BGE-M3/Chroma |
| Dataset Excel | **12 demo cases** in UI; **`make eval-escalate`** scores escalate vs verde/amarillo/rojo |
| Voice | **Kokoro ONNX TTS** (ES `ef_dora`) + browser STT; `TTS_PROVIDER=browser` rollback |
| Metrics | Tokens from Groq usage; E2E STT→TTS in FE; P50/P95 on call summary — **fill README E2E after a voice run** |
| Deliverables | Diagram + informe + **video script** done; **record video** + optional screenshots |

### Must finish before submit ❌

1. **Record video** following [`docs/guion-video.md`](./docs/guion-video.md); upload link to portal.
2. Optional: drop screenshots into `docs/captures/` for informe §9.
3. Rehearse cold start once with a stopwatch.
4. Optional polish: token rollup; BGE-M3 + Chroma; Piper/Kokoro.

---

## 5. Repository map

```text
tech-sphere-voice-agent/
├── STATUS.md / AGENTS.md / README.md / ARCHITECTURE.md
├── docs/challenge/           ← rubrica + stack (committed mirrors)
├── official-kit/             ← gitignored; make kit-clone
├── samples/
├── backend/app/
│   ├── agent/                ← service, factory, llm_groq, llm_gemini, llm_mock, safety
│   ├── rag/                  ← store, extract (PDF), service
│   ├── calls/ / voice/ / api/
│   └── scripts/ingest_official_kit.py
└── frontend/src/
```

---

## 6. Runtime contracts

Unchanged agent JSON: `reply`, `sources[]`, `patient_state`, `escalate`, `escalate_reason`, `model_id`, `latency_ms`.

Env (`backend/.env`):

```env
LLM_PROVIDER=groq   # or gemini | mock
MODEL_ID=llama-3.3-70b-versatile
GROQ_API_KEY=
GEMINI_API_KEY=
BACKEND_PORT=8001
```

---

## 7. How to run

```bash
make setup && make kit-clone
make backend    # :8001
make frontend   # :5173
make ingest-kit ARGS='--scenario cholecystitis --limit 8'
make test
```

Demo script: voice call → clinical question cites PDF → upload/delete custom doc → escalate phrase → hang-up summary.

---

## 8. Architecture decisions

1. Text-first core; voice as adapter (browser today).
2. Ports/adapters for LLM + knowledge.
3. Safety not only LLM (`safety.py`).
4. Prefer **Groq Llama** for voice latency; Gemini if long-context RAG wins.
5. Kit dataset gitignored (size); docs mirrored under `docs/challenge/`.
6. Backend on 8001.

---

## 9. Work plan (now → 10 ago)

1. ~~Build + docs + video script~~
2. **You:** record + upload video (`docs/guion-video.md`).
3. Optional screenshots; stopwatch cold-start rehearsal.
4. Optional: token usage rollup in logs.

### Prompt for a new Cursor chat

```text
Read STATUS.md, docs/challenge/stack-tecnico.md, docs/challenge/rubrica-evaluacion.md.
LLM must be Groq Llama or Gemini Flash (not Anthropic).
Continue Tech Sphere voice agent toward Aug 10 delivery.
Priority: <fill: groq wire / ingest PDFs / Excel scenarios / metrics / video>.
```

---

## 10. Definition of “ready to submit”

- [x] Allowed LLM declared in informe (`llama-3.3-70b-versatile` / Groq)
- [ ] Official PDFs ingested; citations visible in demo/video
- [ ] All eliminatory checks pass (deliverables, cold start, allowed LLM, voice, live knowledge)
- [x] README ≤15 min setup (+ initial metrics; tokens still thin)
- [x] Diagram + informe linked (screenshots + video still open)
- [x] Public MIT repo; incremental commits
- [ ] Hot knowledge + escalate proven on video

Until video is recorded and linked: **not final submission**.
