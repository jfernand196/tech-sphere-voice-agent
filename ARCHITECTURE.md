# Arquitectura

## Capas

```text
UI (React)
  hooks: useCallSession, useAgentVoice
  components: CallPanel, ChatMessage, VoiceControls, KnowledgeConsole
        │ /api/*
        ▼
API (FastAPI routers)     ← adapters de entrada
        │
        ▼
Use-cases                 ← AgentService, CallService, KnowledgeService
        │ depends on ports
        ▼
Ports (Protocol)          ← LLMClient, KnowledgePort
        │
        ▼
Adapters                  ← MockLLM / GroqLLM / GeminiLLM (vía PromptedLLMClient), LocalVectorStore
```

**G3:** solo familias permitidas (Gemini Flash, Llama/Groq, Llama/Phi local). Ver `docs/challenge/stack-tecnico.md`.

## SOLID (cómo se aplica)

| Principio | Aplicación |
|---|---|
| **S**ingle Responsibility | `safety.py` (escalate), `parsing.py` (JSON/sources), `llm_*` (HTTP provider), hooks FE por concern |
| **O**pen/Closed | Nuevo LLM = subclase de `PromptedLLMClient` + rama en `factory.py`; `AgentService` no cambia |
| **L**iskov | `MockLLMClient` y subclases de `PromptedLLMClient` cumplen `LLMClient` |
| **I**nterface Segregation | Ports chicos (`LLMClient`, `KnowledgePort`), no god-interfaces |
| **D**ependency Inversion | `AgentService` depende de Protocols; el wiring está en `api/deps.py` |

## DRY / Clean Code

- Un solo contrato de turno en `schemas.py` (BE) y `types.ts` (FE)
- Reglas de alarma centralizadas en `safety.py` (usadas por mock + guardrail post-LLM)
- UI de llamada separada de orquestación de estado (hooks)

## Tests

```bash
cd backend && . .venv/bin/activate && PYTHONPATH=. python -m pytest tests -q
```
