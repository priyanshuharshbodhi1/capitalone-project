# Project Kisan Agent API (FastAPI + LangGraph)

This service is independent from the frontend and provides an agentic backend with:
- Minimal LangGraph-like orchestration (router → tools → composer)
- Redis checkpointer for short-term memory
- Weather and Market tools with citations
- SSE endpoint to stream responses to the UI

## Requirements
- Python 3.10+
- Redis running locally (or provide REDIS_URL)
- (Optional) Postgres with pgvector if you plan to add RAG later

## Environment
Create a `.env` in `server/` (do not commit):

```
GEMINI_API_KEY=your_key_here
DATA_GOV_IN_API_KEY=optional_key
REDIS_URL=redis://localhost:6379/0
PG_DSN=postgresql://user:pass@localhost:5432/kisan  # optional
CORS_ALLOW_ORIGINS=http://localhost:5173
```

## Install and Run (Quick Start)
```
# 1) Create and activate a virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install backend dependencies
pip install -r server/requirements.txt

# 3) Start Redis (pick ONE)
# 3A) Docker (recommended). Use project name "shetkari" for the container:
docker run -p 6379:6379 --name shetkari-redis -d redis:7
# If port 6379 is already in use on your host, bind another host port (e.g. 6380):
# docker run -p 6380:6379 --name shetkari-redis -d redis:7

# 3B) Local install (no Docker)
# macOS (Homebrew): brew install redis && brew services start redis
# Linux (apt): sudo apt install redis-server && sudo systemctl start redis-server

# 4) Configure environment (create server/.env)
# Use 6379 if you used the default binding above; use 6380 if you changed host port.
cat > server/.env <<'EOF'
REDIS_URL=redis://localhost:6379/0
CORS_ALLOW_ORIGINS=http://localhost:5173
# Optional:
# GEMINI_API_KEY=your_key
# DATA_GOV_IN_API_KEY=your_key
# PG_DSN=postgresql://user:pass@localhost:5432/kisan
EOF

# If you started Redis on host port 6380 instead, update REDIS_URL to:
# redis://localhost:6380/0

# 5) Run the API
uvicorn server.api.main:app --reload --port 8000
```

Health check:
```
curl http://localhost:8000/health
```

## Frontend configuration
- In the frontend `.env`, set:
```
VITE_AGENT_API_URL=http://localhost:8000
```
- Restart the Vite dev server after changing env.

## Streaming Chat (SSE)
Example request using `curl` (SSE prints event stream):
```
curl -N -X POST http://localhost:8000/agent/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Weather tomorrow"}],
    "context": {"lat": 12.9716, "lon": 77.5946, "days": 3, "session_id": "demo"}
  }'
```

Market example (works with or without data.gov API key — demo data otherwise):
```
curl -N -X POST http://localhost:8000/agent/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "messages": [{"role": "user", "content": "Tomato price in Hubballi this week"}],
    "context": {"commodity": "Tomato", "state": "Karnataka", "market": "Hubballi", "session_id": "demo"}
  }'
```

## How it works
- `agent/graph.py` builds the run sequence.
- `nodes/router.py` classifies intent (weather | market | general).
- `tools/weather.py` calls Open‑Meteo; `tools/market.py` calls data.gov.in (Agmarknet) or returns demo data.
- `nodes/composer.py` uses Gemini 1.5 Pro (if key present) to compose a natural answer strictly from tool outputs; otherwise falls back to a simple deterministic text.
- `agent/memory/checkpointer.py` stores session state in Redis.

## Extending
- Add more tools in `agent/tools/` and call from `agent/graph.py` based on router output.
- Add RAG (pgvector) by creating `agent/memory/vector_store.py` and wiring it in the composer.
- Add WebSocket route for bi‑directional streaming if preferred over SSE.

## Troubleshooting
- **Docker port 6379 already in use**: Run Redis on a different host port and update `REDIS_URL`.
  - Recreate container on 6380:
    - `docker rm -f shetkari-redis || true`
    - `docker run -p 6380:6379 --name shetkari-redis -d redis:7`
    - Set `REDIS_URL=redis://localhost:6380/0` in `server/.env`.
- **Container name already in use**: Remove the old container or use a different name.
  - `docker rm -f shetkari-redis`
- **No chatbot response**:
  - Ensure backend is running: `curl http://localhost:8000/health` should return `ok`.
  - Ensure Redis is reachable on the port in `REDIS_URL`.
  - Ensure frontend `.env` has `VITE_AGENT_API_URL=http://localhost:8000` and the dev server has been restarted.
  - Check browser Network tab for `POST /agent/stream` with `text/event-stream` responses.
