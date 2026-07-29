# Instructions for AI coding agents

Before changing anything in this repository:

1. Read **[`STATUS.md`](./STATUS.md)** end-to-end (challenge context, done/todo, contracts, runbook).
2. Skim **[`ARCHITECTURE.md`](./ARCHITECTURE.md)** and **[`README.md`](./README.md)**.
3. Prefer extending ports/adapters over bloating `AgentService`.
4. Do not invent the mandatory challenge LLM id/provider before the official 2026-08-07 tech sheet.
5. Keep Spanish (Colombia) as the patient-facing language.
6. Preserve the agent turn JSON contract in `backend/app/schemas.py`.
7. Use small commits / feature branches when possible.

If `STATUS.md` conflicts with older chat memory, **trust `STATUS.md`** and update it when you complete meaningful work.
