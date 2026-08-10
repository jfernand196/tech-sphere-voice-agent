.PHONY: setup backend frontend dev seed-check kit-clone ingest-kit export-demo eval-escalate test smoke-groq verify warm-embed warm-kokoro

# Kokoro TTS needs Python ≥3.10 (onnxruntime≥1.20). Prefer 3.12 when present.
PYTHON ?= $(shell command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)

setup:
	cd backend && $(PYTHON) -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
	cd frontend && npm install
	cp -n .env.example backend/.env || true
	$(MAKE) warm-embed
	$(MAKE) warm-kokoro

# Pre-download ONNX MiniLM (~220 MB) so cold-start clock doesn't pay the first-embed download.
warm-embed: ## Pre-download embedding model
	cd backend && . .venv/bin/activate && PYTHONPATH=. python -c "from app.rag.embeddings import FastembedEmbedder; FastembedEmbedder().warmup(); print('warm-embed OK')"

# Download Kokoro int8 (~88 MB) + voices (~27 MB) and warm ONNX.
warm-kokoro: ## Pre-download Kokoro TTS model
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/warm_kokoro.py

backend:
	cd backend && . .venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

frontend:
	cd frontend && npm run dev

# Cold-start check: API up + allowed LLM ready (run after make backend).
verify:
	@curl -sf http://127.0.0.1:8001/health | python3 -c 'import sys,json; d=json.load(sys.stdin); ready=bool(d.get("llm_ready")); print("status=%s llm_ready=%s llm_provider=%s model_id=%s" % (d.get("status"), str(ready).lower(), d.get("llm_provider"), d.get("model_id"))); sys.exit(0 if ready else 1)'

# Official artifacts: https://github.com/TechSphere2026/ParticipantArtifacts
kit-clone:
	@if [ -d official-kit/dataset ]; then echo "official-kit already present"; \
	else git clone --depth 1 https://github.com/TechSphere2026/ParticipantArtifacts.git official-kit; fi

# Ingest clinical PDFs into local RAG (requires kit-clone + setup). Example:
#   make ingest-kit ARGS='--scenario cholecystitis --limit 8'
ingest-kit:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/ingest_official_kit.py $(ARGS)

# Rebuild samples/demo_patients.json from official-kit Excels (colecistectomía mix).
export-demo:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/export_demo_patients.py

# Escalate eval vs kit labels (rojo must escalate). Example: make eval-escalate ARGS='--provider mock'
eval-escalate:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/eval_escalate.py $(ARGS)

seed-check:
	curl -s http://127.0.0.1:8001/health && echo && curl -s http://127.0.0.1:8001/knowledge/documents | python3 -m json.tool

test:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python -m pytest tests -q

# Paso 1: verifica que Groq responde (requiere GROQ_API_KEY en backend/.env)
smoke-groq:
	cd backend && . .venv/bin/activate && PYTHONPATH=. python scripts/smoke_groq.py
