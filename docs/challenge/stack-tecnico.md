# Stack técnico — propuesta de stack abierto

Este documento reúne el conjunto de herramientas propuesto para el reto: piezas abiertas
o con nivel gratuito que eliminan la barrera del costo, para que la competencia se decida
por la **arquitectura y la experiencia de usuario** y no por el presupuesto de cada
participante.

**El stack es abierto con una sola excepción: el modelo de lenguaje** (§1). Orquestación,
voz, RAG y embeddings los eliges tú; las herramientas que siguen son sugerencias, no
obligaciones, y puedes usar otras si lo consideras.

---

## 1. Los modelos permitidos

El modelo de lenguaje que razona en tu agente debe pertenecer a **una de estas familias**,
corriendo en su **nivel gratuito** (nube) o **local** según el caso:

| Familia | Dónde corre | Detalle |
|---|---|---|
| **Google Gemini**, gama Flash | Nube, nivel gratuito | [§2](#2-inferencia-en-la-nube-niveles-gratuitos) |
| **Meta Llama** (vía Groq) | Nube, nivel gratuito | [§2](#2-inferencia-en-la-nube-niveles-gratuitos) |
| **Meta Llama** (serie 3.x, 1B–3B) | Local, CPU | [§3](#3-modelos-locales-para-cpu) |
| **Microsoft Phi Mini** (serie 3.5+, ~3–4B) | Local, CPU | [§3](#3-modelos-locales-para-cpu) |

Elige el que prefieras según tu arquitectura. **Tu informe final debe declarar el modelo
exacto que usaste (nombre y versión) y por qué lo elegiste.** Usar un modelo fuera de estas
familias descalifica la entrega (compuerta G3 de la
[rúbrica](rubrica-evaluacion.md#g3--usas-uno-de-los-modelos-permitidos)).

La lista fija familias, no versiones puntuales, porque los proveedores retiran o
reemplazan snapshots sin previo aviso.

> **Nota — los modelos vencen, las familias no.** Los modelos de la tabla son una
> referencia del momento en que se publicó este documento, no una lista congelada de IDs
> exactos. Es normal que alguno ya no esté disponible para cuando estés construyendo (por
> ejemplo, Gemini 1.5 Flash puede haber sido reemplazado por una generación Flash más
> reciente).
>
> Si un modelo sugerido ya no existe, usa el sucesor vigente **de la misma familia y
> proveedor**: la versión más reciente de Llama disponible en Groq, la generación actual
> de Gemini Flash en Google, o la versión más nueva de Llama o Phi Mini local vía Ollama o
> Hugging Face. Puedes apoyarte en [arena.ai](https://arena.ai/) para comparar el
> desempeño de las alternativas vigentes **dentro de las familias permitidas** — no lo
> uses para elegir entre todos los modelos del ranking, muchos son de proveedores fuera de
> la lista. Si tienes dudas sobre si un modelo específico califica, pregunta a la
> organización antes de construir tu solución sobre él.
>
> Esto no cambia cómo se revisa la compuerta G3: lo que se evalúa es que el modelo
> pertenezca a una de las familias permitidas y esté vigente en su nivel gratuito o local,
> no que coincida un identificador exacto de versión.
>
> *Fuentes sobre arena.ai (antes LMArena / Chatbot Arena, comparación de modelos por
> votación humana):
> [arena.ai](https://arena.ai/) ·
> [Arena (AI platform) — Wikipedia](https://en.wikipedia.org/wiki/Arena_(AI_platform)) ·
> [LMArena — Wikipedia](https://en.wikipedia.org/wiki/LMArena)*

La lista de familias es cerrada —aunque la versión exacta dentro de cada una sea
flexible— porque el costo del modelo no debe decidir el reto: con las mismas opciones
sobre la mesa, la diferencia la hace la ingeniería.

Lo demás no está restringido. El reconocimiento de voz, la síntesis de voz, la base
vectorial, los embeddings y el framework de orquestación son decisión tuya, uses o no las
herramientas de este documento.

---

## 2. Inferencia en la nube (niveles gratuitos)

Para razonamiento complejo o ventanas de contexto grandes sin hardware local costoso.

### Google Gemini, gama Flash

Su ventaja competitiva es la **ventana de contexto grande** (del orden de 1 millón de
tokens en los modelos Flash recientes): permite cargar múltiples guías de práctica
clínica, protocolos de triaje y el historial completo del paciente en una sola consulta,
sin fragmentar la información en exceso, lo que preserva la coherencia del razonamiento
médico.

El nivel gratuito de Google AI Studio impone un límite de solicitudes por minuto —revisa
el vigente para el modelo Flash que elijas—, suficiente para desarrollar y para la
demostración en vivo.

→ [Google AI Studio](https://aistudio.google.com/)

### Groq Cloud — latencia ultra-baja

Fundamental cuando la prioridad es la fluidez de la conversación. Sus unidades de
procesamiento de lenguaje (LPU) entregan tokens a velocidad casi instantánea y eliminan
el lag de la interacción.

Da acceso gratuito a modelos potentes de la familia **Llama** (revisa cuáles tiene
disponibles en cada momento) y, sobre todo, a **Whisper Large V3** para transcripción de
voz a texto. Procesar el audio en milisegundos permite que el agente responda casi en
cuanto el paciente termina de hablar.

→ [Consola de Groq (Llama & Whisper)](https://console.groq.com/)

---

## 3. Modelos locales para CPU

Modelos de lenguaje pequeños (SLM) optimizados para correr en computadores comunes, sin
GPU dedicada.

### Llama, serie 3.x (1B y 3B)

Los modelos más eficientes de Meta para computación de borde. El de **1B parámetros
consume ~1.2 GB de RAM**, lo que permite resumir notas clínicas y hacer triaje básico de
forma 100 % privada y local, incluso en laptops de gama media-baja. Usa la versión más
reciente de esta serie disponible al momento de tu entrega.

→ [Descargar vía Ollama](https://ollama.com/library/llama3.2)

### Phi Mini, serie 3.5+ (~3–4B)

El modelo de Microsoft diseñado para razonamiento lógico superior. Pese a su tamaño,
compite con modelos dos o tres veces más grandes en capacidad de seguir instrucciones
complejas y de adherirse a protocolos médicos estrictos sin desviarse. Usa la versión más
reciente de esta serie disponible al momento de tu entrega.

→ [Ver en Hugging Face](https://huggingface.co/microsoft/Phi-3.5-mini-instruct)

### Ollama — orquestador

La pieza que vuelve trivial correr modelos locales: gestiona la descarga y la
cuantización, y expone una API local compatible con el estándar de OpenAI, lo que
facilita integrarla con cualquier interfaz web o móvil.

→ [Instalar Ollama](https://ollama.com/)

---

## 4. Gestión de conocimiento médico (RAG)

El modelo no necesita entrenamiento médico: necesita acceso a fuentes confiables. El RAG
le permite "leer" guías oficiales en tiempo real.

### ChromaDB — local y gratis

Base de datos vectorial de código abierto que corre localmente. Permite indexar miles de
páginas de literatura médica, vademécums y protocolos de emergencia sin costo de
servidores. Es ligera y se integra con Python o JavaScript.

→ [Documentación de ChromaDB](https://www.trychroma.com/)

### BGE-M3 — embeddings en español

El componente crítico para la precisión. BGE-M3 es un modelo de embeddings multilingüe
que sobresale en español: entiende sinónimos médicos y conceptos complejos en nuestro
idioma, lo que asegura que lo recuperado del RAG sea realmente relevante para la consulta
del paciente.

→ [Ver BGE-M3 en Hugging Face](https://huggingface.co/BAAI/bge-m3)

### El flujo de conocimiento

1. Consulta del paciente en español.
2. BGE-M3 busca en ChromaDB el protocolo pertinente.
3. Se inyecta el texto médico recuperado al modelo.
4. Respuesta fundamentada, sin alucinaciones.

---

## 5. Interfaces de voz en español

Alternativas locales y gratuitas a servicios comerciales, optimizadas para la prosodia y
la acentuación del español médico.

### Kokoro-82M — alta calidad

Una revelación en síntesis de voz (TTS): pese a su tamaño mínimo, ofrece una calidad que
rivaliza con modelos comerciales pesados. Soporta voces en español nativo que manejan
correctamente la entonación clínica y, por lo ligero, genera audio en tiempo real sin GPU
potente. Útil para que el agente suene empático y profesional al dar instrucciones.

→ [Demo en español](https://huggingface.co/spaces/leonelhs/kokoro-tts-spanish) ·
[Repositorio base](https://huggingface.co/hexgrad/Kokoro-82M)

### Piper — voces regionales, local-first

Diseñado para ser ultra-rápido en hardware limitado (desde una Raspberry Pi hasta una
laptop de oficina). Ofrece modelos preentrenados para acentos específicos de México y
España. Su ventaja principal es la **latencia mínima**: el audio empieza a reproducirse
casi en el mismo instante en que se genera el texto, algo vital para una conversación
fluida.

→ [Piper en GitHub](https://github.com/rhasspy/piper)

---

## 6. Viabilidad en hardware común

Los modelos recomendados (1B a 3B parámetros) corren en una laptop estándar de **8 a
16 GB de RAM**. No hace falta hardware de servidor especializado.

| Componente | RAM aproximada |
|---|---:|
| Sistema operativo | 3.2 GB |
| Llama serie 3.x (1B) *o* Phi Mini serie 3.5+ (~3–4B) | 1.2 GB / 2.8 GB |
| Voz (Kokoro / Piper) | 0.6 GB |
| RAG (ChromaDB + aplicación) | 0.9 GB |

Los dos modelos locales son alternativas entre sí, no componentes simultáneos: corres uno
u otro.

**RAM mínima 8 GB · procesamiento en CPU · costo de APIs y modelos: $0 · arquitectura
abierta.**

---

Este stack es una base de referencia, no una imposición: fuera de la lista de modelos
permitidos, resuelve la arquitectura como prefieras. Lo que se evalúa es cómo resuelves
los retos de arquitectura, la precisión en la recuperación de información médica y la
calidad de la interacción con el paciente.
