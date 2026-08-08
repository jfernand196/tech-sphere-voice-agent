.PHONY: setup backend frontend dev seed-check kit-clone ingest-kit test smoke-groq

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	cp -n .env.example backend/.env || true

backend:
	cd backend && . .venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

frontend:
	cd frontend && npm run dev

# Official artifacts: https://github.com/TechSphere2026/ParticipantArtifacts
kit-clone:
	@if [ -d official-kit/dataset ]; then echo "official-kit already present"; \
	else git clone --depth 1 https://github.com/TechSphere2026/ParticipantArtifacts.git official-kit; fi

# Ingest clinical PDFs into local RAG (requires kit-clone + setup). Example:
#   make ingest-kit ARGS='--scenario cholecystitis --limit 8'
ingest-kit:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/ingest_official_kit.py $(ARGS)

seed-check:
	curl -s http://127.0.0.1:8001/health && echo && curl -s http://127.0.0.1:8001/knowledge/documents | python3 -m json.tool

test:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python -m pytest tests -q

# Paso 1: verifica que Groq responde (requiere GROQ_API_KEY en backend/.env)
smoke-groq:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/smoke_groq.py
