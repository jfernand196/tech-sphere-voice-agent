# Tech Sphere 2026 — Agente de voz post-operatorio (scaffold)

Scaffold para el **Tech Sphere Challenge 2026**: agente de seguimiento post-operatorio con conversación (texto + voz en navegador), RAG clínico, consola de conocimiento en caliente, trazabilidad de fuentes, lógica de escalate y resumen estructurado de llamada.

> Stack libre. El **LLM es único y obligatorio** (se anuncia el 7 de agosto). Hoy corre en modo `mock` para que puedas desarrollar sin API key.

## Qué incluye

| Módulo | Ruta | Qué hace |
|---|---|---|
| Config | `backend/app/config.py` | `MODEL_ID` / provider vía env |
| Ports | `backend/app/ports.py` | Contratos `LLMClient` / `KnowledgePort` (DIP) |
| RAG | `backend/app/rag/` | Subir / buscar / borrar docs (vector store local) |
| Agent | `backend/app/agent/` | Orquestación + adapters LLM + safety/parsing |
| Calls | `backend/app/calls/` | Historial + resumen al colgar |
| Voice | `backend/app/voice/` | Seam para STT/TTS server-side (MVP usa browser) |
| UI | `frontend/src/` | Hooks + componentes (llamada / conocimiento) |

Arquitectura y mapeo SOLID: ver [`ARCHITECTURE.md`](./ARCHITECTURE.md).

```bash
make test   # pytest (safety rules)
```

## Requisitos

- Python 3.9+ (recomendado 3.11+)
- Node.js 20+
- Chrome/Edge recomendado para micrófono (Web Speech API)

## Arranque (< 15 min)

```bash
cd tech-sphere-voice-agent
make setup

# terminal 1 — API en 8001 (8000 suele estar ocupado por otras apps locales)
make backend

# terminal 2
make frontend
```

- API: http://127.0.0.1:8001/docs  
- UI: http://127.0.0.1:5173  

Si cambias el puerto del backend: `VITE_API_TARGET=http://127.0.0.1:PUERTO npm run dev`

Al iniciar, se siembra un protocolo genérico de ejemplo si no hay documentos.

## Demo rápida de las 5 piezas del reto

1. **Conversación adaptativa** → pestaña *Llamada* → Iniciar → escribe o usa *Hablar*.
2. **RAG** → pregunta por fiebre / herida; la respuesta cita el protocolo.
3. **Conocimiento en caliente** → pestaña *Conocimiento* → sube un `.txt` → vuelve a preguntar → cita el nuevo doc → elimínalo → ya no lo usa.
4. **Trazabilidad** → cada respuesta del agente lista `sources` (doc + chunk).
5. **Escalate + resumen** → di “no puedo respirar” o “quiero un doctor” → alerta → *Colgar* → JSON de resumen.

## Configurar el LLM obligatorio (7 ago)

Copia `.env.example` a `backend/.env` y ajusta:

```env
LLM_PROVIDER=anthropic
MODEL_ID=<el-modelo-de-la-ficha-tecnica>
ANTHROPIC_API_KEY=sk-ant-...
```

El cliente Anthropic ya está cableado en `backend/app/agent/service.py`. Si el provider obligatorio es otro, cambia solo esa capa — el contrato JSON del agente no cambia.

## API principal

- `GET /health`
- `POST /calls/start`
- `POST /calls/{id}/turn` `{ "call_id", "message" }`
- `POST /calls/{id}/end`
- `GET/POST/DELETE /knowledge/documents`
- `POST /knowledge/query`
- `GET /voice/capabilities`

## Contrato del agente (cada turno)

```json
{
  "reply": "...",
  "sources": [{"doc_id":"...","title":"...","chunk_id":"...","excerpt":"..."}],
  "patient_state": {"symptoms": [], "severity": "none|mild|moderate|severe"},
  "escalate": false,
  "escalate_reason": null
}
```

## Roadmap sugerido (3 días del challenge)

1. Conectar dataset (Delta Share) + reemplazar seed.
2. Endurecer RAG (pgvector/Chroma) y parseo PDF.
3. STT/TTS server-side si el browser no alcanza latencia.
4. Métricas P50/P95, tokens y costo en README.
5. Diagrama, informe, video demo; prueba de cold start &lt; 15 min.

## Licencia

MIT (alineada con la entrega del challenge).
