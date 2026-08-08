# Instructions for AI coding agents

Before changing anything in this repository:

1. Read **[`STATUS.md`](./STATUS.md)** end-to-end (challenge context, done/todo, contracts, runbook).
2. Skim **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** and **[`README.md`](./README.md)**.
3. Read the official rules mirrors under **[`docs/challenge/`](./docs/challenge/)** (`stack-tecnico.md`, `rubrica-evaluacion.md`). Full dataset lives in `./official-kit` via `make kit-clone`.
4. Prefer extending ports/adapters over bloating `AgentService`.
5. **LLM constraint:** only allowed families — Gemini Flash (free), Llama via Groq (free), local Llama 3.x 1B–3B, local Phi Mini 3.5+. **Anthropic/Claude is not allowed.** Prefer `LLM_PROVIDER=groq` for voice latency.
6. Keep Spanish (Colombia) as the patient-facing language.
7. Preserve the agent turn JSON contract in `backend/app/schemas.py`.
8. Use small commits / feature branches when possible.

If `STATUS.md` conflicts with older chat memory, **trust `STATUS.md`** and update it when you complete meaningful work.
