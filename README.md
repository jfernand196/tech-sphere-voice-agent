# Tech Sphere 2026 — Agente de voz post-operatorio

Agente de seguimiento post-operatorio: conversación de voz (navegador), RAG clínico, consola de conocimiento en caliente, citas de fuentes, escalate a humano y resumen estructurado.

> **Handoff:** lee [`STATUS.md`](./STATUS.md) primero.  
> **Reglas oficiales:** [`docs/challenge/`](./docs/challenge/) (rúbrica + stack). Kit completo: [TechSphere2026/ParticipantArtifacts](https://github.com/TechSphere2026/ParticipantArtifacts).

## Decisión que más pesa (G3)

El stack de orquestación/voz/RAG es libre. **El modelo de lenguaje no:**

| Permitido (gratis / local) | No permitido |
|---|---|
| Gemini Flash (AI Studio) | Claude / Anthropic |
| Llama vía Groq | GPT de pago / otros fuera de lista |
| Llama 3.x 1B–3B o Phi Mini local (Ollama) | |

Usar un modelo fuera de esa lista **descalifica**. Detalle: [`docs/challenge/stack-tecnico.md`](./docs/challenge/stack-tecnico.md).

Recomendación de este repo: **Groq + Llama** (latencia para voz). Alternativa: **Gemini Flash** (contexto largo).

## Paso 1 — Activar Groq (obligatorio para el reto)

1. Crea una API key gratis en https://console.groq.com/keys  
2. En `backend/.env` (ya viene con `LLM_PROVIDER=groq`):

```env
LLM_PROVIDER=groq
MODEL_ID=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_tu_key_aqui
```

3. Verifica que el modelo responde:

```bash
make smoke-groq
```

Debes ver `OK — Groq respondió.` Si dice que falta la key, pégala y reintenta.  
4. Reinicia el backend. En `GET /health` debe salir `"llm_ready": true` y `"llm_provider": "groq"`.

Sin key, el backend **no** finge estar en Groq (evita entregar en `mock` por error).

## Arranque (< 15 min)

```bash
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent
make setup
# edita backend/.env → GROQ_API_KEY=...
make smoke-groq

# Kit oficial (~127MB, gitignored) — dataset + 107 PDFs clínicos
make kit-clone

# terminal 1
make backend    # http://127.0.0.1:8001

# terminal 2
make frontend   # http://127.0.0.1:5173
```

Opcional — indexar corpus clínico del kit en el RAG local:

```bash
make ingest-kit ARGS='--scenario cholecystitis --limit 8'
```

Adapters: `backend/app/agent/llm_groq.py`, `llm_gemini.py`. Factory: `factory.py`.

## Qué incluye

| Módulo | Qué hace |
|---|---|
| RAG | Upload `.txt/.md/.pdf`, listar, borrar; retrieval local |
| Agent | Orquestación + safety + JSON contract |
| Calls | Historial + resumen al colgar |
| Voice | Web Speech en el navegador (STT/TTS) |
| UI | Consola de conocimiento + interfaz de llamada |

## Demo de las 5 piezas

1. **Voz** → pestaña Llamada → Hablar / escuchar.
2. **RAG** → pregunta clínica; respuesta con `sources`.
3. **Conocimiento vivo** → sube PDF/txt → pregunta → borra → ya no lo usa.
4. **Escalate** → “no puedo respirar” / “quiero un doctor”.
5. **Resumen** → Colgar → JSON + tarjeta.

## Tests

```bash
make test
```

## Entrega (7–10 ago)

Compuertas: 4 entregables · levantable ≤15 min · modelo permitido · voz realtime · upload/delete conocimiento.  
Puntos: ver [`docs/challenge/rubrica-evaluacion.md`](./docs/challenge/rubrica-evaluacion.md).
