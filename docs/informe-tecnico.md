# Informe técnico — Tech Sphere Challenge 2026

**Entregable 03.** Evidencia de proceso, configuración, prompts y declaración del modelo.  
**Repositorio:** https://github.com/jfernand196/tech-sphere-voice-agent  
**Diagrama (entregable 02):** [`../ARCHITECTURE.md`](../ARCHITECTURE.md)  
**Cold start:** [`../README.md`](../README.md)  
**Fecha:** 2026-08-08

---

## 1. Resumen ejecutivo

Se implementó un **agente de voz en el navegador** para seguimiento post-operatorio en español (Colombia). El paciente habla o escribe; el agente recupera conocimiento clínico (RAG), responde citando fuentes, decide si **escalar a un humano** y, al colgar, genera un **resumen estructurado**.

La solución se levanta en **≤15 minutos** siguiendo únicamente el README (`make setup` → clave Groq → `make backend` / `make frontend` → `make verify`).

---

## 2. Declaración del modelo (obligatorio — G3)

| Campo | Valor |
|---|---|
| **Familia permitida** | Meta **Llama** vía **Groq** (nivel gratuito) |
| **Modelo exacto** | `llama-3.3-70b-versatile` |
| **Provider en código** | `LLM_PROVIDER=groq` |
| **Adapter** | `backend/app/agent/llm_groq.py` |
| **Factory** | `backend/app/agent/factory.py` (bloquea Anthropic/Claude) |

### Por qué lo elegimos

1. **Latencia para voz.** En un agente conversacional, el cuello de botella percibido es el tiempo hasta la respuesta hablada. Groq + Llama 70B en free tier entrega turnos de agente en torno a **P50 ≈ 1.5 s / P95 ≈ 2.2 s** en nuestra muestra de evaluación (`make eval-escalate`, 10 casos).
2. **Cumple la lista cerrada del reto.** Familia Llama en Groq está explícitamente permitida; Anthropic/Claude descalifica.
3. **JSON estable con temperatura baja (0.2)** para el contrato `AgentTurnResponse`.
4. **Alternativa evaluada y descartada como default:** Gemini Flash — mejor ventana de contexto para RAG largo, pero priorizamos latencia de turno para la demo de voz. Queda cableada (`LLM_PROVIDER=gemini`) por si el corpus crece.
5. **Local Llama/Phi (Ollama)** — descartado para la entrega principal por fricción de instalación en el cold start del jurado (≤15 min).

---

## 3. Arquitectura (mapa al código)

Ver diagrama completo en [`ARCHITECTURE.md`](../ARCHITECTURE.md). Resumen:

| Pieza | Decisión | Dónde |
|---|---|---|
| Orquestación | FastAPI use-cases + ports/adapters | `backend/app/agent/`, `ports.py` |
| Voz | Web Speech API en el browser (STT + TTS) | `frontend/src/speech.ts` |
| RAG | Store local, upload/delete en caliente, PDF | `backend/app/rag/` |
| Escalate | Prompt + **guardrails post-LLM** (autoritativos) | `prompts.py` + `safety.py` |
| Persistencia de llamadas | JSON en `DATA_DIR` | `backend/app/calls/` |

Principio de diseño: el LLM **no es la única fuente de verdad** para alarmas clínicas. Las reglas en `safety.py` pueden forzar `escalate=true` aunque el modelo diga lo contrario (asimetría: falso negativo es catastrófico).

---

## 4. Configuración

Plantilla: [`.env.example`](../.env.example) → `backend/.env`.

```env
LLM_PROVIDER=groq
MODEL_ID=llama-3.3-70b-versatile
GROQ_API_KEY=gsk_...
CORS_ORIGINS=http://localhost:5173
DATA_DIR=./data
```

Puertos: API **8001**, UI **5173**. Verificación: `make smoke-groq` y `make verify`.

Dependencias fijadas: `backend/requirements.txt`, `frontend/package.json`.

---

## 5. Prompts

Fuente: `backend/app/agent/prompts.py`.

### System prompt (extracto)

```
Eres un agente de voz de seguimiento post-operatorio en español (Colombia).
Tu trabajo es:
1) Conversar con empatía y claridad sobre síntomas post-operatorios.
2) Fundamentar respuestas clínicas SOLO en el conocimiento recuperado (RAG).
3) Citar documentos usados.
4) Decidir si hay que alertar a un humano (escalate).

Reglas de seguridad:
- Si no hay evidencia en el contexto RAG, di que no tienes esa información y ofrece escalar.
- No inventes protocolos, dosis ni diagnósticos.
- Escala (escalate=true) ante signos de alarma: dificultad respiratoria, dolor intenso no controlado,
  sangrado abundante, fiebre alta persistente, confusión, dolor torácico, vómito incoercible,
  signos de infección grave, o si el paciente pide hablar con un humano.

Responde SIEMPRE en JSON con esta forma exacta:
{ "reply", "sources", "patient_state", "escalate", "escalate_reason" }
```

### User prompt (estructura)

Por turno se inyecta: nombre, procedimiento, día post-op, historial reciente (≤8 turnos), chunks RAG y el mensaje actual (`build_user_prompt`).

### Iteración de prompts / seguridad

| Hallazgo | Ajuste |
|---|---|
| El modelo a veces no escalaba infecciones (secreción + fiebre) | Composites en `safety.py` (fiebre + herida; dolor alto + fiebre) |
| Pedidos explícitos de médico | Keywords `quiero un doctor` / `hablar con un humano` fuerzan escalate |
| Etiquetas kit rojo/verde | Harness `make eval-escalate` → hard accuracy **1.0** (mock y Groq) |

---

## 6. Flujo de decisión (escalate)

1. RAG recupera `top_k=4` chunks.  
2. LLM propone JSON con `escalate`.  
3. `apply_safety_overrides` evalúa el mensaje del paciente; si hay alarma, **fuerza** escalate y sube severidad.  
4. Al colgar, `CallService.end` agrega si hubo escalate en cualquier turno.

Evaluación vs etiquetas oficiales del kit (colecistectomía):

| Métrica | Resultado (Groq / mock) |
|---|---|
| Rojo escalados | 2/2 |
| Falsos positivos verde | 0/4 |
| Hard accuracy | 1.0 |

---

## 7. Conocimiento vivo (G5)

Desde la consola de administración (pestaña Knowledge):

1. **Upload** `.txt` / `.md` / `.pdf` → chunk + index local.  
2. El agente **cita** el documento en `sources` cuando responde.  
3. **Delete** → chunks eliminados; el agente deja de usar ese material.

Al arrancar el backend se siembra un protocolo genérico de alarma (`main.py` → `seed_sample_knowledge`) para que el cold start tenga RAG básico sin clonar el kit. Los PDFs oficiales se indexan opcionalmente con `make ingest-kit`.

---

## 8. Métricas observadas

| Métrica | Valor | Método |
|---|---|---|
| Latencia turno agente P50 | ~1.5 s | `latency_ms`, 10 turnos Groq (`eval-escalate`) |
| Latencia turno agente P95 | ~2.2 s | Idem |
| Invocaciones LLM / turno | 1 | Un completion por mensaje |
| Consultas RAG / turno | 1 | `retrieve` antes del LLM |
| Costo estimado / llamada (~6 turnos) | ~$0–0.01 | Free tier Groq en el reto; precios lista de producción muy bajos para turnos cortos |

La latencia punta-a-punta de voz añade STT + TTS del navegador encima del turno de agente.

---

## 9. Capturas del demo

Añadir aquí (o en `docs/captures/`) pantallas tomadas de la UI local:

| # | Captura sugerida | Qué demuestra |
|---:|---|---|
| 1 | Call tab · paciente demo rojo día 7 | Setup + caso kit |
| 2 | Turno con `sources` visibles | RAG + citas |
| 3 | Knowledge · documento subido | Conocimiento vivo (upload) |
| 4 | Mismo documento eliminado + pregunta | Olvido tras delete |
| 5 | Banner / flag de escalate | Decisión de alerta |
| 6 | Resumen al colgar | Call summary estructurado |
| 7 | `make verify` en terminal | Cold start / LLM ready |

```bash
# Cómo generar capturas en 2 minutos
make backend    # terminal 1
make frontend   # terminal 2
# Abrir http://127.0.0.1:5173 → recorrer checklist del README → guardar PNGs en docs/captures/
```

---

## 10. Cómo se usó asistencia de IA en el proceso

- Scaffold inicial FastAPI + React y cables de RAG/voz.  
- Iteración de `safety.py` contra etiquetas del kit.  
- Documentación de cold start y este informe.  
- Criterio humano: decisiones de modelo (Groq), asimetría clínica (guardrails), y calibración con `eval-escalate`.

El historial de commits en GitHub refleja el trabajo incremental (PRs de adapters, UX demo, eval, README).

---

## 11. Riesgos y trabajo futuro

| Riesgo | Mitigación actual | Si hubiera 2 semanas más |
|---|---|---|
| Alucinación clínica | Prompt “solo RAG” + no inventar dosis | Mejor retrieval (BGE-M3 + Chroma) |
| Falso negativo escalate | Guardrails post-LLM + eval rojo | Más casos capa2 ruidosa; umbrales por procedimiento |
| Rate limit Groq free | Reintentos en eval; demo corta | Cola / Gemini fallback automático |
| Voz solo browser | Documentado; Chrome/Edge | Piper/Kokoro o Whisper server-side |
| Tokens no agregados en README | `latency_ms` sí; usage Groq pendiente | Rollup tokens in/out por turno en logs |

---

## 12. Checklist de entregables

| # | Entregable | Estado |
|---|---|---|
| 01 | Repositorio público + README levantable | Sí |
| 02 | Diagrama arquitectura + flujo de decisión | [`ARCHITECTURE.md`](../ARCHITECTURE.md) |
| 03 | Este informe (modelo + por qué + prompts) | Este documento |
| 04 | Video demo + 2 preguntas a cámara | Pendiente |

Compuertas: G2 (cold start) documentada · G3 (modelo) declarada aquí · G4/G5 se demuestran en video y sesión en vivo.
