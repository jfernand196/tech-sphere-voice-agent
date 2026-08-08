# Rúbrica de evaluación — Tech Sphere Challenge 2026

Este documento explica **cómo se evalúa tu entrega**: qué requisitos son eliminatorios,
sobre qué se reparten los 100 puntos, qué debe reportar tu README y cómo se ejecuta la
evaluación.

El punto de partida del reto está en el [README](../README.md); los datos, en
[`dataset/`](../dataset/).

---

## 1. Estructura de la evaluación

La evaluación tiene **dos fases**:

1. **Compuertas eliminatorias** (§3). Son binarias: se cumplen o no se cumplen.
2. **Puntuación sobre 100** (§4), repartida en seis criterios.

**Lo que no pasa las compuertas no se puntúa.** No hay puntaje parcial por una entrega
que no se puede levantar, que no habla, o que usa un modelo fuera de la lista permitida.

Cuatro principios rigen toda la calificación:

- **Solo cuenta lo observable.** Se califica lo que el jurado ve correr, lo que está en
  los logs, lo que dice tu README y lo que muestra tu video. Las intenciones no puntúan.
- **La estética no puntúa.** Las dos superficies de tu solución —consola de
  administración e interfaz de llamada— son contratos funcionales mínimos, no piezas de
  diseño. Nadie gana ni pierde puntos por lo bonita que sea la interfaz.
- **Asimetría clínica.** En salud, el falso negativo —no alertar cuando había que
  alertar— es la falla catastrófica. Pesa más que el falso positivo.
- **Mismas condiciones para todos.** Toda entrega se evalúa con los mismos insumos
  estandarizados y el mismo protocolo cronometrado.

---

## 2. Los 4 entregables

| # | Entregable | Qué debe contener |
|---|---|---|
| **01** | **Repositorio** | Público en GitHub, con tu implementación completa, README y dependencias declaradas. Debe poder ser levantado por el jurado siguiendo tu documentación. |
| **02** | **Diagrama** | Arquitectura de tu solución y flujo de decisión del agente. |
| **03** | **Informe final** | Evidencia de tu proceso: prompts, configuraciones, capturas del demo, y la declaración explícita de qué modelo usaste y por qué lo elegiste. |
| **04** | **Video** | Demo funcional con grabación de pantalla, más dos preguntas de cierre respondidas frente a cámara. |

### Las dos preguntas de cierre del video

**Pregunta 1.** Si debes convencer a un cliente de que adopte el agente que
construiste, ¿cómo presentarías el problema que resuelve, por qué tu solución es la
adecuada y qué valor diferencial ofrece frente a otras alternativas?

**Pregunta 2.** Elige la decisión técnica más relevante que tomaste (arquitectura,
modelo, herramientas, prompts, RAG, memoria, manejo del contexto, etc.) y cuéntanos:
¿qué alternativas evaluaste?, ¿por qué las descartaste?, ¿qué riesgos identificaste?, y
si tuvieras dos semanas más para mejorar la solución, ¿qué cambiarías y por qué?

El **informe final no tiene un criterio propio** en §4: es requisito eliminatorio y es la
evidencia con la que se sustenta la evaluación del criterio *Repositorio, proceso y
buenas prácticas*.

---

## 3. Las 5 compuertas eliminatorias

### G1 — Entregas los 4 entregables completos

Repositorio, diagrama, informe final y video. Se verifica antes de agendar cualquier
sesión de evaluación.

**Si falla:** la entrega no se evalúa.

### G2 — Tu solución es levantable en ≤15 minutos

Siguiendo únicamente tu README —credenciales, URLs y accesos incluidos— la solución
queda corriendo y accesible en 15 minutos o menos.

**Cómo se verifica:** el levantamiento se ejecuta cronometrado siguiendo tu README al
pie de la letra. Si el procedimiento no llega a buen puerto, o si queda duda sobre si la
solución está realmente en pie, se coordina una sesión contigo para que ejecutes el
levantamiento paso a paso; el cronómetro corre igual, sobre el mismo procedimiento que
documentaste. Esa sesión es parte del procedimiento normal de verificación, no una
segunda oportunidad: lo que se cronometra es siempre lo que documentaste.

**Qué no cuenta contra estos 15 minutos:** las pruebas de la evaluación. El reloj mide
el levantamiento, no la sesión.

**Si falla:** la entrega no se evalúa. Si lo que falla son credenciales o accesos rotos,
se te contacta una vez, tienes 24 horas para corregir y hay un solo reintento.

### G3 — Usas uno de los modelos permitidos

El modelo de lenguaje de tu agente debe ser uno de los listados en
[`stack-tecnico.md`](stack-tecnico.md#1-los-modelos-permitidos). El resto del stack
—orquestación, voz, RAG, embeddings— es libre.

Tu informe final debe declarar **cuál usaste y por qué lo elegiste**. Se verifica además
contra tus dependencias, tu configuración y tu código.

**Si falla:** la entrega queda descalificada.

### G4 — La conversación de voz en tiempo real funciona

El jurado habla y el agente responde con voz. Se verifica con un intercambio mínimo:
saludo y una pregunta trivial.

**Si falla:** la entrega no se evalúa. El reto es de voz; un chatbot de texto no compite.

### G5 — El conocimiento vivo funciona desde tu consola

Subes un documento desde tu consola de administración y el agente lo usa; lo eliminas y
el agente lo olvida. Se verifica con un documento de prueba que no forma parte de
ningún corpus entregado.

**Si falla:** la entrega no se evalúa.

### Reglas comunes a las cinco compuertas

- Fallar cualquier compuerta significa que la entrega **no se puntúa**. Usar un modelo
  fuera de la lista permitida, además, **descalifica**.
- Cada compuerta fallida se documenta con evidencia y **recibes la razón exacta**.
- La de credenciales rotas en G2 es la única corrección contemplada. No hay otras.

---

## 4. Los 6 criterios de puntuación

| Puntos | Criterio |
|---:|---|
| 20 | RAG, precisión clínica y conocimiento vivo |
| 20 | Lógica de decisión y escalamiento |
| 15 | Comprensión del problema y diseño de la conversación |
| 15 | Calidad de la conversación (voz) |
| 15 | Video de argumentación y demo |
| 15 | Repositorio, proceso y buenas prácticas |
| **100** | **Total** |

Cada criterio se descompone internamente en sub-criterios con descriptores que el jurado
aplica de forma uniforme sobre todas las entregas. Se publica el peso de cada criterio;
el desglose fino no.

### 20 pts · RAG, precisión clínica y conocimiento vivo

Qué se observa:

- Si las respuestas clínicas del agente reflejan el corpus de conocimiento que tiene
  cargado, y si lo hacen de forma demostrable o solo genéricamente correcta.
- Qué hace el agente ante una pregunta cuya respuesta no está en su conocimiento: si
  declara el límite y redirige, o si improvisa.
- Cómo se comporta el conocimiento cuando cambia: qué pasa al incorporar material nuevo
  y qué queda —o no queda— cuando ese material se elimina.
- Si cada respuesta clínica puede rastrearse hasta el documento que la sustenta, y si
  esa referencia resiste una verificación contra la fuente real.

### 20 pts · Lógica de decisión y escalamiento

Qué se observa:

- Cómo clasifica el agente la criticidad de lo que reporta el paciente, en situaciones
  donde escalar es claramente lo correcto, donde claramente no lo es, y en situaciones
  ambiguas.
- Qué hace ante la ambigüedad: si indaga antes de decidir, si decide sin indagar, o si
  no decide.
- Qué produce el sistema cuando decide alertar: qué queda registrado, con qué estructura
  y con qué persistencia, y qué se le comunica al paciente sobre el siguiente paso.
- Qué queda al terminar la llamada: si existe un resumen que identifique al paciente y
  su procedimiento, los síntomas reportados, la decisión tomada, las referencias usadas y
  los próximos pasos.

### 15 pts · Comprensión del problema y diseño de la conversación

Qué se observa:

- Cómo abre, conduce y cierra el agente la conversación; qué pasa cuando el paciente se
  sale del guion; cómo entrega instrucciones largas.
- Qué parte de lo que el reto pide quedó cubierta, qué quedó sin cubrir, y qué se
  construyó por fuera de lo pedido.
- Si tu diagrama corresponde a lo que realmente implementaste. El jurado toma elementos
  del diagrama al azar y los busca en el código.

### 15 pts · Calidad de la conversación (voz)

Qué se observa:

- El tono y el registro del agente en un contexto de salud, y la longitud de sus
  respuestas.
- La latencia de la conversación, contrastada entre lo que reportas en tu README y lo
  que ocurre en la sesión, y qué hace tu solución durante los silencios.
- Cómo se comporta el agente ante entradas adversas: interrupciones, audio degradado,
  jerga regional, pacientes hostiles o asustados, peticiones ajenas a su misión e
  intentos de manipular sus instrucciones.

### 15 pts · Video de argumentación y demo

Qué se observa:

- Qué muestra tu demo y cómo lo muestra: si el material permite juzgar el funcionamiento
  real de la solución, y si corresponde al repositorio que entregaste.
- Tu respuesta a la Pregunta 1: cómo articulas el problema, la solución y su valor frente
  a las alternativas.
- Tu respuesta a la Pregunta 2: la decisión técnica que elegiste, las alternativas que
  evaluaste, los riesgos que identificaste y qué harías con más tiempo.

### 15 pts · Repositorio, proceso y buenas prácticas

Qué se observa:

- Si tu repositorio es reproducible: documentación de instalación y arquitectura,
  estructura, historia de commits y dependencias fijadas.
- Si tu solución es observable: si las métricas de §5 están reportadas, si son
  verificables en los logs y si concuerdan con lo que ocurre en la sesión.
- Qué rastro dejó tu proceso de trabajo: cómo trabajaste con IA, cómo evaluaste y
  ajustaste tus prompts y respuestas, y si el informe final es coherente con el
  repositorio.

---

## 5. Qué debe reportar tu README

Estas métricas son obligatorias. No son opcionales ni "deseables": si no están, el
apartado correspondiente de §4 se califica muy por debajo de su tope, aunque tu solución
funcione bien.

**Latencia de respuesta** — P50 y P95, medidos desde que el paciente termina de hablar
hasta que empieza a sonar el audio del agente.

**Consumo** — tokens de entrada y salida por turno y por llamada, invocaciones al modelo
por turno, y consultas al RAG por llamada.

**Costo estimado por llamada.** Si tu solución corre local, extrapola a precios de API de
producción y explica el cálculo.

Lo que reportes se contrasta con lo que ocurre en la sesión de evaluación y con tus
logs. Reportar números que no se sostienen es peor que no reportarlos.

---

## 6. Conductas que penalizan

Más allá de la calificación por criterio, estas conductas restan de forma explícita:

- **Alucinación clínica peligrosa** — inventar una dosis, un medicamento o un
  procedimiento, o tranquilizar al paciente ante un síntoma de alarma. Cada ocurrencia
  penaliza y queda registrada textualmente en el acta.
- **No alertar cuando había que alertar.** Un falso negativo en un escenario donde
  escalar era claramente lo correcto limita severamente la calificación de *Lógica de
  decisión y escalamiento*, y la reincidencia puede anularla.
- **Caer en una inyección de prompt** — que el agente obedezca instrucciones que
  contradicen su misión. Anula el apartado correspondiente de *Calidad de la
  conversación (voz)* y se anota textualmente.
- **Métricas inconsistentes con los logs** de la sesión. Limita severamente la
  calificación de *Repositorio, proceso y buenas prácticas*.
- **Un demo que no corresponde al repositorio entregado.** Levanta una bandera de
  integridad, que revisa el panel completo de jurados.

---

## 7. Cómo se ejecuta la evaluación

**Una sesión evaluada en vivo**, con insumos estandarizados e idénticos para todos los
participantes: preguntas con respuesta conocida contra el corpus, escenarios de decisión
interpretados por el jurado, entradas adversas y una prueba de conocimiento vivo con
material que tu agente no habrá visto antes. La sesión tiene una duración acotada e
idéntica para todos y sigue el mismo protocolo en todos los casos.

**Al menos dos jurados** evalúan cada entrega de forma independiente aplicando los
mismos descriptores; el puntaje final es el promedio. Si dos jurados divergen de forma
significativa en el total, un tercer jurado revisa el acta y los logs.

**Desempates**, en este orden: mayor puntaje en el núcleo funcional (RAG y precisión
clínica + lógica de decisión y escalamiento); menor costo por llamada reportado *y*
verificado; decisión del panel.

**Banderas de integridad** —demo que no corresponde al repositorio, métricas fabricadas—
las revisa el panel completo antes de cualquier decisión.

Parte de la evaluación ocurre fuera de la sesión: video, repositorio, informe, diagrama y
el contraste entre las métricas de tu README y tus logs.

---

## 8. Después de la rúbrica

Esta rúbrica de 100 puntos determina **quiénes son los 3 finalistas**.

El orden de los ganadores lo decide un panel de expertos el **5 de septiembre de 2026**,
durante el evento de premiación de Tech Sphere. Los finalistas sustentan en vivo: el panel
dicta qué probar en el momento y **no se acepta demo pregrabado**. Esa etapa no suma
puntos a esta rúbrica.
