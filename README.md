# Agente de voz post-operatorio — Tech Sphere 2026

Agente de voz en el navegador para seguimiento post-operatorio en español de Colombia. El paciente habla o escribe; el agente busca en protocolos, cita la fuente, puede **alertar a un humano** y al colgar deja un resumen.

Se levanta en **≤15 minutos** solo con la sección *Cold start*. El modelo de la llamada es **Llama 3.3 70B en Groq**.

| | |
|---|---|
| Repositorio | https://github.com/jfernand196/tech-sphere-voice-agent |
| Modelo (default) | Groq + Llama `llama-3.3-70b-versatile` |
| Pantalla | http://127.0.0.1:5173 |
| API | http://127.0.0.1:8001 |

Rúbrica: [`docs/challenge/`](./docs/challenge/).

## Cómo leer esto

| Si buscas… | Ve a… |
|---|---|
| Levantar la app en ≤15 min | Esta página, *Cold start* |
| Recuadros, un turno, alerta | [`ARCHITECTURE.md`](./ARCHITECTURE.md) |
| Modelo, prompts, métricas, capturas | [`docs/informe-tecnico.md`](./docs/informe-tecnico.md) |

## Entregables

| # | Entregable | Enlace |
|---|---|---|
| 01 | Repositorio + este README | https://github.com/jfernand196/tech-sphere-voice-agent |
| 02 | Arquitectura y flujo de decisión | https://github.com/jfernand196/tech-sphere-voice-agent/blob/main/ARCHITECTURE.md |
| 03 | Informe técnico | https://github.com/jfernand196/tech-sphere-voice-agent/blob/main/docs/informe-tecnico.md |
| 04 | Video demo + 2 preguntas a cámara | https://drive.google.com/file/d/1rjx0qMlYmtqqT44bNZotweVjgCvfxkXE/view?usp=sharing |

---

## Cold start (≤ 15 minutos)

Este es el **único** camino para parar el reloj de G2. De arriba a abajo.

- **Cuenta en los 15 min:** clonar → `make setup` → clave → smoke → backend + frontend → `make verify` → abre la UI.
- **No cuenta:** demo de micrófono, subir/borrar docs, alerta, kit oficial, eval, refrescar métricas.

### Antes del reloj (2–3 min)

Instala una vez en la máquina (herramientas, no la app):

| Herramienta | Versión | Comprobar |
|---|---|---|
| macOS o Linux | — | — |
| Git | reciente | `git --version` |
| Make | cualquiera | `make --version` |
| Python | **3.12** (3.10+ vale) | `python3.12 --version` |
| Node.js | **18+** | `node -v` |
| npm | viene con Node | `npm -v` |
| Chrome o Edge | reciente | micrófono / Web Speech |

**Clave gratis:** https://console.groq.com/keys — tenla lista para pegar. No hace falta plan de pago.

### Camino cronometrado — copiar y pegar

```bash
# 1) Clonar
git clone https://github.com/jfernand196/tech-sphere-voice-agent.git
cd tech-sphere-voice-agent

# 2) Instalar deps y crear backend/.env (~3–8 min con red normal)
#    Prefiere python3.12. Baja MiniLM (~220 MB) y voces TTS opcionales
#    para que el primer arranque del API no pague esas descargas.
make setup

# 3) Pega tu clave Groq en backend/.env
#      LLM_PROVIDER=groq
#      MODEL_ID=llama-3.3-70b-versatile
#      GROQ_API_KEY=gsk_...tu_clave...
#    El resto de líneas déjalas como están.

# 4) Comprueba que el modelo contesta (debe imprimir OK)
make smoke-groq

# 5) Arranca el API (terminal 1) — déjala abierta
make backend
#    Esperado: Uvicorn en http://127.0.0.1:8001
#    Log: [rag] index ready: docs=… chunks=…

# 6) Arranca la UI (terminal 2) — déjala abierta
make frontend
#    Esperado: Vite en http://127.0.0.1:5173
```

### Listo — para el reloj cuando todo esto sea verdad

En una **tercera** terminal:

```bash
make verify
```

Debes ver algo así:

```text
status=ok llm_ready=true rag_ok=true docs=… chunks=… llm=groq/llama-3.3-70b-versatile
```

Abre **http://127.0.0.1:5173** — pestañas Llamada y Conocimiento.

Eso es “solución en pie y accesible” para G2.  
**No** gastes reloj en micrófono, subidas ni alerta: eso es la demo **después** de levantar.

### Si algo falla

| Qué ves | Qué hacer |
|---|---|
| `make smoke-groq` → falta la clave | Pon `GROQ_API_KEY` en `backend/.env` (sin comillas). Vuelve a correr smoke. |
| `llm_ready=false` | Clave mal o `LLM_PROVIDER` no es `groq`. Arregla `.env` y reinicia `make backend`. |
| `rag_ok=false` / docs pero 0 trozos | Reinicia `make backend` y espera `[rag] index ready`. |
| Puerto 8001 o 5173 ocupado | Cierra el otro proceso (`make frontend` usa `:5173` estricto). |
| No encuentra `python3` / `npm` | Instala Python 3.12 + Node 18+; otra vez `make setup`. |
| La primera búsqueda tarda | `make setup` ya baja MiniLM (`warm-embed`). Sin red: `EMBED_PROVIDER=hash` (peor significado; no es el modo demo). |
| Micrófono / voz | Chrome o Edge; permite el mic; localhost vale (no hace falta HTTPS). |
| `kokoro-onnx` falla en Python 3.9 | Usa 3.12: `rm -rf backend/.venv && make setup`. La voz de salida por defecto es la del **navegador**. |
| Groq HTTP **429** | El plan gratis se llenó. Espera ~30 s y reintenta. No es un bug del agente. |

Si `LLM_PROVIDER=groq` y no hay clave, el backend **no** se pasa solo a `mock`.

---

## Modelos permitidos (G3)

Orquestación, voz y documentos son libres. **El modelo que escribe el turno no:**

| Permitido | No permitido |
|---|---|
| Gemini Flash (AI Studio) | Claude / Anthropic |
| Llama en Groq | GPT de pago y otras familias |
| Llama 3.x 1B–3B o Phi Mini local (Ollama) | |

Default de este repo: **Groq + Llama**. Alternativa: `LLM_PROVIDER=gemini` + `GEMINI_API_KEY` (`.env.example`). Detalle: [`docs/challenge/stack-tecnico.md`](./docs/challenge/stack-tecnico.md).

---

## Después de levantar — demo de 2 minutos (fuera del reloj)

Cuando `make verify` pase y la UI esté abierta:

1. **Llamada** → elige un paciente demo (p. ej. día 7 · crítico) o edita uno libre.
2. Habla o escribe un síntoma de la pista en pantalla (la pista es para el actor; **no** se manda al modelo).
3. Pregunta de cuidado clínico → la respuesta debe mostrar **fuentes**.
4. **Conocimiento** → sube un `.txt` / `.pdf` chico → pregunta por él → **Eliminar** → el agente deja de usarlo.
5. Di “no puedo respirar” o “quiero un doctor” → **alerta a humano**.
6. **Colgar** → resumen (latencias / tokens).

La voz de salida por defecto es la del **navegador** (rápida). Kokoro / Piper son opt-in si corriste `make warm-kokoro` / `make warm-piper`.

Al arrancar el backend se carga un protocolo genérico de alarma (alcanza para levantar y citar algo). Los PDFs oficiales del kit son optativos (siguiente sección).

---

## Optativo — kit oficial (no entra en el cold start)

```bash
make kit-clone                                          # ~127MB, no va a git
make ingest-kit ARGS='--scenario cholecystitis --limit 8'
make export-demo                                        # refresca el catálogo de pacientes
make eval-escalate ARGS='--provider mock'               # examen de alerta, sin API
make eval-escalate                                      # lo mismo con el LLM de .env (Groq)
```

Meta del examen: **todo rojo debe alertar**; en verde, pocos falsos positivos. Amarillo se anota y **no** entra en la nota dura.  
Resultados: `samples/eval_escalate_results.json` (no va a git).

---

## Métricas (rúbrica §5) — después de levantar

Van instrumentadas en código. Los números de abajo son de **una** llamada de voz; se refrescan en la tarjeta al colgar (no forma parte del cold start).

| Métrica | Qué mide aquí |
|---|---|
| **Latencia de voz (oficial)** | El paciente deja de hablar → empieza el audio del agente |
| **Latencia del turno** | Backend: búsqueda + modelo + reglas (`latency_ms`) |
| **Tokens** | `usage` de Groq (o Gemini) |
| **Llamadas al modelo / búsquedas** | **1** y **1** por cada mensaje del paciente |
| **Costo** | Precio de lista Groq Llama 3.3 70B; en el plan gratis el runtime sale ≈ $0 |

P50 = la mitad de los turnos fueron más rápidos que ese valor. P95 = el 95 % quedó por debajo.

### Muestra (10 turnos con micrófono)

Groq `llama-3.3-70b-versatile` · voz del navegador para oír y para hablar · caso día 7 crítico.

| Métrica | Valor |
|---|---|
| Voz P50 / P95 | **1136 / 1427 ms** |
| Turno (backend) P50 / P95 | **1044 / 1337 ms** |
| Modelo / búsqueda por turno | **1 / 1** |
| Tokens entrada / salida | **8422 / 2208** |
| Costo estimado / llamada | **$0.0067 USD** |

Para refrescar: una llamada de ≥10 turnos con mic → Colgar → lee P50/P95 en el resumen. Detalle: [`docs/informe-tecnico.md`](./docs/informe-tecnico.md).

---

## Qué hay en el código

| Pieza | Qué hace |
|---|---|
| Documentos | Subir `.txt/.md/.pdf`, listar, borrar; búsqueda local + citas |
| Agente | Arma el turno + reglas de alerta + JSON |
| Llamadas | Historial y resumen al colgar |
| Voz | El navegador pasa voz a texto y, por defecto, lee la respuesta. Kokoro / Piper opt-in |
| Pantalla | Llamada + Conocimiento |

El dibujo y el mapa a archivos: [`ARCHITECTURE.md`](./ARCHITECTURE.md).

## Pruebas

```bash
make test          # unitarias / API
make smoke-app     # humo en vivo (el backend tiene que estar arriba)
make rehearse-jury # RAG · fuera de tema · G5 · alerta · inyección (backend arriba)
```
