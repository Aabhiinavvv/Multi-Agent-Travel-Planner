# TripMate AI — Multi-Agent Travel Planner

TripMate AI provides two implementations of the travel-planning workflow:

- **TypeScript application (primary):** Express, React, Vite, Gemini, specialist agents, approval/revision flow.
- **Python application (recovered):** FastAPI, LangGraph, Groq, Tavily MCP, AviationStack MCP, Weather MCP, supervisor and guardrails, specialist agents, PostgreSQL checkpointing, and human approval.

The implementations are maintained as separate services. They share the project but do not share session storage.

## TypeScript application (primary)

Requirements: Node.js 22 or newer.

```bash
npm ci
cp .env.example .env
# Add GEMINI_API_KEY to .env to enable Gemini (fallback mode works without it).
npm run dev
```

Open http://localhost:3000.

Build and run the production server:

```bash
npm run build
npm start
```

The build compiles the Vite frontend and a NodeNext-compatible server bundle into `dist-server/`. The production server serves the built frontend from `dist/`.

## Python + LangGraph application (optional)

Requirements: Python 3.11, plus the credentials for the external services you intend to use.

Create and activate an environment, then install dependencies:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Configure these values in `.env` before creating travel plans:

- `GROQ_API_KEY` — required for the Python LLM agents.
- `TAVILY_API_KEY` — hotel/web search via Tavily MCP.
- `AVIATIONSTACK_API_KEY` — aviation information via AviationStack MCP.
- `OPENWEATHER_API_KEY` — current weather and forecast via the custom Weather MCP server.

Run the Python API from the repository root:

```bash
python -m uvicorn tools.app:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000. The health endpoint is http://127.0.0.1:8000/health.

### Python checkpoint storage

Set `DATABASE_URL` to a PostgreSQL connection string for durable LangGraph checkpoints. This is recommended for deployments because human-approval sessions must survive process restarts and be available to the process that handles the approval request.

When `DATABASE_URL` is not set, the Python app uses an in-memory checkpointer for local development and tests. **In-memory sessions are lost on restart and are not suitable for multi-worker production deployments.**

### Docker

The default `Dockerfile` builds the primary TypeScript application:

```bash
docker build -t tripmate-ai .
docker run --rm -p 3000:3000 --env-file .env tripmate-ai
```

The recovered Python API has its own Dockerfile:

```bash
docker build -f Dockerfile.python -t tripmate-ai-python .
docker run --rm -p 8000:8000 --env-file .env tripmate-ai-python
```

Provide `DATABASE_URL` for durable Python approval sessions. Do not commit the real `.env` file.

## Agent architecture

- **Supervisor Agent:** interprets the trip request and selects relevant specialists.
- **Input Guardrail:** blocks unrelated requests.
- **Flight Agent:** airport, airline, and route guidance.
- **Hotel Agent:** accommodation and neighborhood search.
- **Weather Agent:** current weather and short-range forecast.
- **Budget Agent:** budget feasibility and cost categories.
- **Itinerary Agent:** combines specialist findings into a draft.
- **Human-in-the-Loop:** pauses for approval or revision feedback.
- **Final Agent:** produces the final itinerary after review.

## Verification

GitHub Actions runs the following checks on pushes and pull requests to `main`:

- TypeScript type check and Vite + production-server build.
- TypeScript development API draft/approval smoke test.
- Compiled production Node server smoke test.
- Python syntax compilation, import/startup tests, and mocked LangGraph human-approval/revision tests.
- Docker builds for both service images.

External API credentials and a live PostgreSQL instance are not required by the automated mock tests. Live provider integration still depends on valid keys, network access, and provider-side availability.
