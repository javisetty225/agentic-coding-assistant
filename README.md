# ⚡ Agentic Coding Assistant

> **Generate Langflow pipelines and custom Python components from a single sentence — in under 30 seconds.**

---

## What is it?

An **agentic coding assistant** that replaces hours of manual Langflow development
with a single natural language description.

```
Without the agent:                    With the agent:
──────────────────                    ───────────────
Open Langflow UI      (5 min)         Type one sentence
Drag boxes manually   (20 min)                ↓
Connect arrows        (10 min)        Agent runs ~16 tool calls
Write Python component(30 min)                ↓
Write docs            (10 min)        3 files generated ✅
───────────────────────────────
Total: ~75 minutes                    Total: 30 seconds
```

---

## Architecture

**Pi coding-agent style** (extensible tool harness).

```
You type a description
        │
        ▼
src/main.py  ──────────────────→  CLI mode
        │
src/backend/app/  ─────────────→  REST API mode (FastAPI)
        │
        ▼
src/agent/orchestrator.py  ────→  Agent loop + 7 tools
        │
        ▼
src/agent/flow_builder.py  ────→  Correct Langflow structures
        │
        ▼
src/generated/  ───────────────→  flow.json + component.py + README.md
```

### Why Pi over Pydantic Monty?

Langflow artifact generation is **exploratory** — the agent must decide which
nodes to create, validate iteratively, and fix mistakes. Pi's flexible tool
harness handles this better than a fixed left-to-right execution model.

### The 7 Tools

| Tool | Purpose |
|------|---------|
| `write_file` | Save generated content to workspace |
| `read_file` | Read previously written files |
| `edit_file` | Fix specific parts without full rewrite |
| `list_files` | Check what has been created so far |
| `generate_node_id` | Create unique IDs like `ChatInput-a3f8c921` |
| `validate_flow_json` | Verify flow structure before saving |
| `validate_component_python` | Verify Python component is correct |
| `get_langflow_schema_template` | Get correct starter templates |

---

## Project Structure

```
agentic-coding-assistant/
│
├── src/
│   ├── main.py                           ← CLI entry point
│   │
│   ├── agent/
│   │   ├── orchestrator.py               ← Agent loop + 7 tools + Workspace
│   │   └── flow_builder.py               ← Langflow node/edge/flow helpers
│   │
│   ├── backend/
│   │   └── app/
│   │       ├── main.py                   ← FastAPI create_app() factory
│   │       ├── models/schemas.py         ← Pydantic request/response models
│   │       ├── services/agent_service.py ← Wraps LangflowAgent for REST
│   │       └── routers/
│   │           ├── generate.py           ← POST /api/v1/generate
│   │           ├── history.py            ← GET  /api/v1/history
│   │           └── health.py             ← GET  /health
│   │
│   └── generated/                        ← Created automatically on run
│       ├── flow.json                     ← Import into Langflow UI
│       ├── *.py                          ← Custom Python component
│       └── README.md                     ← Usage instructions
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                       ← Main React UI component
│   │   ├── App.css                       ← Dark terminal aesthetic
│   │   ├── api/client.ts                 ← Typed fetch calls to backend
│   │   ├── hooks/useGenerate.ts          ← Generation state hook
│   │   └── types/api.ts                  ← TypeScript interfaces
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts                    ← Proxies /api → localhost:8000
│
├── tests/
│   └── test_agent.py                     ← 33 tests, all passing
│
├── .github/workflows/ci.yml              ← CI: tests + TS check + Docker build
├── Dockerfile                            ← Serves FastAPI via uvicorn --factory
├── docker-compose.yml                    ← Backend + frontend + CLI profile
├── pyproject.toml                        ← Python dependencies (uv)
└── DECISIONS.md                          ← Architectural rationale
```

## Quick Start

### Option 1 — CLI (simplest)

```bash
git clone https://github.com/javisetty225/agentic-coding-assistant
cd agentic-coding-assistant

uv sync
export ANTHROPIC_API_KEY=sk-ant-...

python src/main.py --interactive
```

### Option 2 — Full Stack (Backend + Frontend)

**Terminal 1 — Backend:**
```bash
cd agentic-coding-assistant
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn src.backend.app.main:create_app --factory --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` ✅

### Option 3 — Docker (everything at once)

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
docker compose up
```

| Service | URL |
|---------|-----|
| Frontend UI | http://localhost:5173 |
| API docs | http://localhost:8000/docs |

### Option 4 — Single shot

```bash
python src/main.py "Build a movie recommendation flow with MovieFilterComponent"
# Files saved to src/generated/
```

---

## Example Prompts

```bash
# Movie intelligence (matches project theme)
"Build a movie recommendation flow with MovieFilterComponent
 for genre and mood filtering then LLM generates recommendations"

# Vision — Bonus multimodal
"Build a vision flow that accepts image uploads and uses
 Claude to classify movie posters into genres"

# Text processing
"Build a text summarization chatbot flow with an OpenAI model"
```

---

## Generated Artifacts

### `flow.json` — Visual Pipeline
Import directly into Langflow: **Import Flow** → select `flow.json`.
All nodes and connections are drawn automatically.

### `*.py` — Custom Python Component
Drop into `~/.langflow/components/` or paste into the Langflow component editor.

---