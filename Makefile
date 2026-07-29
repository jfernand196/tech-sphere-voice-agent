.PHONY: setup backend frontend dev seed-check

setup:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	cp -n .env.example backend/.env || true

backend:
	cd backend && . .venv/bin/activate && PYTHONPATH=. uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

frontend:
	cd frontend && npm run dev

seed-check:
	curl -s http://127.0.0.1:8001/health && echo && curl -s http://127.0.0.1:8001/knowledge/documents | python3 -m json.tool
