# Guion de video — Tech Sphere 2026 (entregable 04)

Duración objetivo: **6–8 minutos** (demo 4–5 min + 2 preguntas a cámara ~2–3 min).  
Idioma: **español**. Grabar pantalla + micrófono; al final, cara a cámara.

Repo que debe verse: https://github.com/jfernand196/tech-sphere-voice-agent  
UI: http://127.0.0.1:5173 · API: http://127.0.0.1:8001

---

## 0. Antes de grabar (checklist, ~5 min)

- [ ] `make backend` y `make frontend` corriendo  
- [ ] `make verify` → `llm_ready=true` / `llm_provider=groq`  
- [ ] Chrome o Edge; micrófono permitido  
- [ ] Volumen TTS ok; pestaña Call + Knowledge listas  
- [ ] Archivo de prueba listo: `samples/protocolo-herida.txt` (o un `.txt` corto inventado con una frase única, p. ej. “Protocolo ZETA-42: lavar herida con solución X”)  
- [ ] Cerrar notificaciones / ocultar API keys en pantalla  
- [ ] Ensayar una vez **sin** grabar

---

## 1. Apertura en pantalla (15–20 s)

**Mostrar:** pestaña del repo en GitHub (README) → luego la UI.

**Decir:**

> Soy [tu nombre]. Esta es mi entrega al Tech Sphere Challenge 2026: un agente de voz para seguimiento post-operatorio. Corre en el navegador, usa Llama 3.3 70B en Groq —modelo permitido—, RAG clínico, consola de conocimiento en caliente, escalate a humano y resumen al colgar. Ahora demuestro el flujo.

---

## 2. Demo en pantalla (≈4 min)

### Bloque A — Llamada + voz (≈60–75 s)

1. Pestaña **Call** → elegir paciente demo **día 7 · rojo** (o similar).  
2. Iniciar llamada.  
3. **Hablar** (o tipear si falla el mic, y mencionar “también soporta texto”): usar la pista del caso o algo natural, p. ej.  
   > Me duele la herida y veo secreción amarilla; creo que tengo fiebre.  
4. Dejar que el agente **responda con voz**. Señalar en UI: respuesta + severidad.

**Decir:**

> El paciente habla; el agente responde en español con Web Speech. El razonamiento lo hace Llama en Groq; la voz es del navegador.

### Bloque B — RAG + citas (≈45–60 s)

1. Preguntar algo clínico cubierto por el protocolo/seed o PDFs ingestados, p. ej.  
   > ¿Qué signos de alarma debo vigilar en la herida?  
2. Señalar **`sources`** / documentos citados en la UI.

**Decir:**

> Las respuestas clínicas se apoyan en RAG. Aquí se ve qué documento sustentó la respuesta —trazabilidad.

### Bloque C — Conocimiento vivo G5 (≈60–75 s) — crítico

1. Ir a **Knowledge**.  
2. **Subir** el `.txt` de prueba con la frase única (ZETA-42 u otra).  
3. Volver a Call (misma llamada o nueva) y preguntar:  
   > ¿Qué dice el protocolo ZETA-42?  
4. Mostrar que responde con esa info / lo cita.  
5. **Borrar** el documento en Knowledge.  
6. Preguntar de nuevo lo mismo → debe **dejar de usarlo** (dice que no tiene esa info o no lo cita).

**Decir:**

> Subo un documento desde la consola y el agente lo aprende. Lo elimino y lo olvida. Eso es el conocimiento vivo que pide el reto.

### Bloque D — Escalate (≈30–45 s) — crítico

1. Decir con claridad:  
   > No puedo respirar.  
   (o) > Quiero hablar con un doctor.  
2. Mostrar `escalate=true` / razón / severidad.  

**Decir:**

> Ante una alarma, el sistema escala a humano. No confío solo en el LLM: hay reglas de seguridad post-modelo para evitar falsos negativos.

### Bloque E — Resumen al colgar (≈20–30 s)

1. **End call** / colgar.  
2. Mostrar tarjeta/JSON de resumen: síntomas, escalate, fuentes, texto.

**Decir:**

> Al colgar queda un resumen estructurado listo para un clínico.

### Cierre de demo (10 s)

> Eso cubre voz en tiempo real, RAG con citas, conocimiento vivo y escalate. El levantamiento en menos de 15 minutos está documentado en el README.

---

## 3. Preguntas a cámara (obligatorias)

Mira a cámara. Puedes tener este texto en un segundo monitor, pero **no leas como robot**.

### Pregunta 1 — Pitch al cliente (≈60–90 s)

**Enunciado oficial:** Si debes convencer a un cliente de que adopte el agente que construiste, ¿cómo presentarías el problema que resuelve, por qué tu solución es la adecuada y qué valor diferencial ofrece frente a otras alternativas?

**Respuesta sugerida (adapta a tu voz):**

> El problema: después de una cirugía, muchos pacientes quedan en casa con dudas y síntomas. Si algo grave pasa de noche, o no saben si es “normal”, el riesgo es llegar tarde a una alerta humana. Un call center clásico no escala; un chatbot de texto no sirve cuando el paciente está mareado o con las manos ocupadas.
>
> Nuestra solución es un agente de **voz** en el navegador, en español colombiano, que conversa, se apoya en protocolos clínicos con RAG y **cita la fuente**, actualiza conocimiento en caliente sin redesplegar, y —lo más importante— decide cuándo **escalar a un humano**, con reglas de seguridad además del modelo.
>
> El diferencial frente a un FAQ o un bot genérico: trazabilidad clínica, conocimiento vivo desde consola, y asimetría de seguridad —preferimos escalar de más antes que callar una alarma. Además corre sobre un LLM permitido y barato (Llama en Groq), así que el valor está en la ingeniería, no en un modelo cerrado caro.

### Pregunta 2 — Decisión técnica (≈90–120 s)

**Enunciado oficial:** Elige la decisión técnica más relevante… alternativas, por qué las descartaste, riesgos, y qué harías con dos semanas más.

**Respuesta sugerida (elige UNA decisión — recomendada: guardrails + Groq):**

> La decisión más relevante fue **no dejar el escalate solo en manos del LLM**. El modelo propone, pero después aplicamos `safety.py`: keywords y composites (por ejemplo fiebre + secreción purulenta) pueden **forzar** escalate. Lo calibramos contra las etiquetas rojo/verde del kit oficial y logramos hard accuracy 1.0 en esa muestra.
>
> Alternativas que evalué: (1) solo prompt —más simple, pero arriesgado en falso negativo; (2) solo reglas —rígido y pobre en conversación; (3) Gemini Flash como default —mejor contexto largo, pero prioricé **latencia de voz** con Groq Llama 3.3 70B. Anthropic ni se consideró: descalifica.
>
> Riesgos: rate limits del free tier; embeddings locales MiniLM vía fastembed (no BGE-M3/Chroma); voz solo browser. Con dos semanas más: Chroma + modelo más grande, rollup de tokens en logs, y TTS/STT más robusto (Whisper/Piper) sin perder el cold start de 15 minutos.

*(Alternativa si prefieres hablar del modelo: misma estructura — por qué Groq Llama vs Gemini vs local.)*

---

## 4. Cierre (10 s, a cámara o pantalla)

> Repo público, diagrama e informe técnico están en GitHub. Gracias.

Pegar en la descripción del video / portal:

- Repo: https://github.com/jfernand196/tech-sphere-voice-agent  
- Diagrama: `ARCHITECTURE.md`  
- Informe: `docs/informe-tecnico.md`  
- Modelo: `llama-3.3-70b-versatile` (Groq)

---

## 5. Errores a evitar (rúbrica)

| Evitar | Por qué |
|---|---|
| Demo solo texto, sin voz del agente | Falla G4 |
| No mostrar upload → uso → delete → olvido | Falla G5 |
| No escalar en alarma clara | Penaliza fuerte decisión |
| Inventar dosis / tranquilizar ante alarma | Penaliza alucinación clínica |
| UI que no sea del repo entregado | Bandera de integridad |
| Leer las preguntas sin mirar cámara | Pierde puntos de argumentación |

---

## 6. Plan B si algo falla en vivo

| Falla | Plan B en cámara |
|---|---|
| Mic / STT | Escribir el turno; decir “STT del browser falló; el contrato de voz TTS sigue activo” y **forzar un speak** del agente |
| Groq 429 | Esperar 20–30 s; reintentar; o turno corto “quiero un doctor” para escalate |
| RAG vacío | Usar el seed + upload del `.txt` ZETA-42 (bloque C salva la demo) |
| Paciente demo raro | Paciente libre: nombre + colecistectomía + día 7 |

Graba **dos tomas** de los bloques C y D; edita la mejor.
