# ⚡ FlowForge AI

> **Generate Langflow pipelines and custom Python components from a single sentence — in under 30 seconds.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Anthropic](https://img.shields.io/badge/Powered%20by-Claude%20Sonnet-orange.svg)](https://anthropic.com)
[![Architecture](https://img.shields.io/badge/Architecture-Pi%20Agent%20Style-purple.svg)](https://github.com/badlogic/pi-mono)

---

## What is FlowForge AI?

FlowForge AI is an **agentic coding assistant** that replaces hours of manual
Langflow development with a single natural language description.

```
Without FlowForge AI:               With FlowForge AI:
────────────────────                ──────────────────
Open Langflow UI      (5 min)       Type one sentence
Drag boxes manually   (20 min)              ↓
Connect arrows        (10 min)      Agent runs 16 tool calls
Write Python component(30 min)              ↓
Write docs            (10 min)      3 files generated  
──────────────────────────────
Total: ~75 minutes                  Total: 30 seconds
```

---

## Live Demo

```bash
git clone https://github.com/your-username/flowforge-ai

uv sync
export ANTHROPIC_API_KEY=sk-ant-...

python src/main.py --interactive
```

Type any description:
```
Describe your Langflow flow: Build a movie recommendation flow with
MovieFilterComponent for genre and mood filtering then LLM generates
personalized recommendations
```

Output:
```
✓  Generation complete
────────────────────────────────────────────────────
   Files generated : 3
   Tool calls made : 16

   Artifacts:
     • MovieRecommenderComponent.py    (10,294 chars)
     • flow.json                       (9,584 chars)
     • README.md                       (6,998 chars)

   Saved to: ./generated/
```

---

## Architecture

FlowForge AI uses the **Pi coding-agent pattern** — an extensible tool harness
where Claude drives itself by calling a flat registry of tools.

```
You type a description
        │
        ▼
main.py → starts the agent
        │
        ▼
orchestrator.py → sends to Claude with 7 tools
        │
        ▼
┌──────────────────────────────────────────┐
│         Agent Loop (max 20 iters)        │
│                                          │
│  Claude picks a tool → agent runs it     │
│  Result sent back → Claude picks next    │
│  Repeats until Claude says "done"        │
└──────────────────────────────────────────┘
        │
        ▼
flow_builder.py → correct Langflow structures
        │
        ▼
generated/ → your files appear here
```

---

## The 7 Tools

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
flowforge-ai/
│
├── src/
│   ├── main.py                    ← Entry point (run this)
│   │
│   ├── agent/
│   │   ├── orchestrator.py        ← Agent loop + tools + workspace
│   │   └── flow_builder.py        ← Langflow node/edge/flow helpers
│   │
│   └── generated/                 ← Created automatically on run
│       ├── flow.json              ← Import into Langflow UI
│       ├── MovieRecommenderComponent.py  ← Custom component
│       └── README.md              ← Usage instructions
│
├── tests/
│   └── test_agent.py              ← 37 tests
│
├── demo/
│   └── index.html                 ← Browser demo
│
├── DECISIONS.md                   ← Architectural rationale
└── pyproject.toml
```

---

## Generated Artifacts

### flow.json — Visual Pipeline
Import directly into Langflow UI with one click.

```
[Genre Input] ──→ ┌─────────────────────┐ ──→ [Recommendations]
                  │  MovieRecommender   │
[Mood Input]  ──→ │     (CineBot)       │ ──→ [Reasoning]
                  └─────────────────────┘
```

### MovieRecommenderComponent.py — Custom Component
A production-quality Langflow component featuring:
- 7 configurable inputs (genre, mood, era, count, model)
- 2 outputs (recommendations + reasoning)
- OpenAI API integration with JSON response parsing
- Smart LLM result caching (one API call for both outputs)
- Full error handling

### VisionAnalyzer.py — Bonus Multimodal Component
Handles images instead of just text:
- Accepts PNG / JPG / WEBP / GIF uploads via `FileInput`
- Base64 encodes images for Claude vision API
- 4 task modes: `describe`, `classify`, `extract_text`, `qa`
- Movie use case: upload a poster → identify genre, cast, mood

---

## Usage Options

```bash
# Interactive mode (keep generating multiple flows)
python main.py --interactive

# Single shot
python main.py "Build a sentiment analysis flow with a custom component"

# Custom output directory
python main.py "Build a RAG flow" --output-dir ./my-output

# Run tests
cd src && python -m pytest ../tests/test_agent.py -v
```

---

## Example Prompts

```
# Text processing
"Build a text summarization chatbot flow with an OpenAI model"

# Movie intelligence
"Build a movie recommendation flow with MovieFilterComponent
 for genre and mood filtering then LLM generates recommendations"

# Sentiment analysis
"Build a sentiment analysis pipeline with a custom
 PolarityDetector component that returns POSITIVE NEGATIVE NEUTRAL"

# Vision / Bonus
"Build a vision flow that accepts image uploads and uses
 Claude to classify movie posters into genres"

# RAG pipeline
"Build a RAG flow with document input text splitter
 embedder vector store retriever LLM and chat output"
```

---

## How to Import into Langflow

```
1. Install Langflow
   pip install langflow

2. Start Langflow
   python -m langflow run

3. Open browser at http://localhost:7860

4. Click Import Flow
   Select src/generated/flow.json

5. Add your OpenAI API key in the flow node

6. Click Run ✅
```

---

## Evaluation — 37 Automated Tests

```
Level 1 — Unit Tests
  Node IDs are unique and correctly formatted
  Nodes have correct Langflow structure
  Edges connect source and target correctly

Level 2 — Validation Tests
  Catches broken JSON
  Catches missing nodes or edges
  Catches invalid Python components

Level 3 — Artifact Tests
  Generated flow.json is valid
  Every edge references a real node
  Python component inherits from Component
  All files exist and are not empty
```

