from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import calls, health, knowledge, voice
from app.api.deps import get_knowledge_service, settings


SAMPLE_PROTOCOL = """Protocolo de seguimiento post-operatorio genérico

Signos de alarma que requieren alerta humana inmediata:
- Dificultad para respirar o dolor en el pecho
- Sangrado abundante por la herida
- Fiebre mayor a 38.5 C que no cede
- Dolor intenso no controlado con la medicación indicada
- Vómito persistente que impide tomar líquidos
- Confusión, desmayo o debilidad extrema

Cuidados rutinarios:
- Mantener la herida limpia y seca
- Cumplir el esquema de analgésicos prescrito
- Caminar con ayuda según indicación médica
- Reportar enrojecimiento, calor local o secreción purulenta

Si el paciente refiere fiebre leve sin otros signos de alarma, indicar hidratación,
reposo relativo y reevaluación en la siguiente hora. Si la fiebre sube o aparecen
escalofríos intensos, escalar a personal capacitado.
"""


def seed_sample_knowledge() -> None:
    ks = get_knowledge_service()
    docs = ks.list_documents()
    seed = next(
        (
            d
            for d in docs
            if d.metadata.get("seed") and d.filename == "protocolo-postop-generico.txt"
        ),
        None,
    )
    if seed and seed.metadata.get("seed_version") == 2:
        return
    if seed:
        ks.delete(seed.doc_id)
    elif docs:
        # User already has knowledge; don't force-insert the sample.
        return

    ks.ingest_text(
        title="Protocolo post-operatorio genérico",
        filename="protocolo-postop-generico.txt",
        text=SAMPLE_PROTOCOL,
        metadata={"seed": True, "seed_version": 2},
    )


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Dirs are created in get_settings(); lifespan only seeds knowledge.
    _ = settings()
    seed_sample_knowledge()
    yield


app = FastAPI(
    title="Tech Sphere Voice Agent",
    description="Scaffold: agente de voz post-operatorio con RAG, consola en caliente y escalate.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(knowledge.router)
app.include_router(calls.router)
app.include_router(voice.router)
