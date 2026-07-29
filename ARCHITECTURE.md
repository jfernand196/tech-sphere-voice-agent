# Arquitectura (scaffold)

```text
Browser (React)
  ├─ CallPanel: texto + Web Speech STT/TTS
  └─ KnowledgeConsole: upload / delete docs
           │  /api/*
           ▼
FastAPI
  ├─ /calls     → CallService (historial + resumen)
  ├─ /knowledge → KnowledgeService + LocalVectorStore
  ├─ /voice     → VoiceService (seam STT/TTS server)
  └─ agent/     → AgentService (mock | Anthropic)
                    │
                    ├─ retrieve RAG chunks
                    ├─ LLM → JSON contract
                    └─ safety rules (escalate)
```

## Contrato de turno

Toda respuesta del agente incluye: `reply`, `sources[]`, `patient_state`, `escalate`, `escalate_reason`.

## Hot knowledge

1. `POST /knowledge/documents` → chunk + embed + persist  
2. Turnos siguientes recuperan el nuevo doc  
3. `DELETE /knowledge/documents/{id}` → borra chunks → retrieval ya no lo ve  

## Qué reemplazar el 7 ago

- `MODEL_ID` / `LLM_PROVIDER` en `.env`
- Seed local → dataset Delta Share
- Embeddings hash → modelo de embeddings real / pgvector
- Browser STT/TTS → proveedor de voz si hace falta latencia
