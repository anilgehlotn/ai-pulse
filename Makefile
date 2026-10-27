# Shortcuts for running AI Pulse. Run `make <target>` from the repo root.
PY = backend/.venv/bin/python

.PHONY: setup seed backend frontend test eval eval-live up down

# Install backend (in backend/.venv) and frontend dependencies.
setup:
	python3 -m venv backend/.venv && $(PY) -m pip install -r backend/requirements.txt
	cd frontend && npm ci

# Wipe the local database and load the demo data (password: pulse123).
seed:
	cd backend && .venv/bin/python -m app.seed

# Run the API on http://localhost:8000, reloading on code changes.
backend:
	cd backend && .venv/bin/python -m uvicorn app.main:app --reload

# Run the web app on http://localhost:5173.
frontend:
	cd frontend && npm run dev

# Run every backend and frontend test.
test:
	cd backend && .venv/bin/python -m pytest -q
	cd frontend && npm test

# Scoring eval with canned AI replies (what CI runs).
eval:
	cd backend && AI_MODE=mock .venv/bin/python -m app.eval

# Scoring eval against a local Ollama model on both case sets. Needs `ollama pull llama3.2`.
eval-live:
	cd backend && AI_MODE=live LLM_API_URL=http://localhost:11434/v1/chat/completions LLM_API_KEY=ollama LLM_MODEL=llama3.2 LLM_JSON_MODE=true .venv/bin/python -m app.eval --set all

# Build and start backend + frontend in Docker (needs SECRET_KEY, see .env.example).
up:
	docker compose up --build

# Stop the containers. The database volume is kept; add -v to delete it.
down:
	docker compose down
