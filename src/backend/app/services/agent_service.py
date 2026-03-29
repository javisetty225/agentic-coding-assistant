"""Agent Service — wraps LangflowAgent for the REST API layer."""

from __future__ import annotations

import os
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Ensure src/ is importable so `from agent.orchestrator import ...` resolves
_SRC = Path(__file__).resolve().parents[3]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from src.agent.orchestrator import LangflowAgent

from ..models.schemas import ArtifactFile, GenerateResponse, ToolCall

# In-memory run store (replace with a real DB in production)
_runs: list[dict] = []


def _file_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    return {"json": "json", "py": "python", "md": "markdown"}.get(ext, "text")


async def run_agent(
    description: str,
    api_key: str | None = None,
) -> GenerateResponse:
    run_id = uuid.uuid4().hex[:8]
    started = time.time()

    resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not resolved_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not configured. "
            "Set the env var or pass api_key in the request body."
        )

    agent = LangflowAgent(api_key=resolved_key)
    raw = agent.run(description)

    duration = round(time.time() - started, 2)
    now = datetime.now(UTC)

    artifacts = [
        ArtifactFile(
            filename=fname,
            content=content,
            size=len(content),
            file_type=_file_type(fname),
        )
        for fname, content in raw.items()
    ]

    tool_calls = [
        ToolCall(
            tool=tc["tool"],
            input=tc["input"],
            result=str(tc["result"])[:400],
        )
        for tc in agent.tool_calls_log
    ]

    response = GenerateResponse(
        run_id=run_id,
        status="success",
        description=description,
        artifacts=artifacts,
        tool_calls=tool_calls,
        tool_call_count=len(tool_calls),
        file_count=len(artifacts),
        duration_seconds=duration,
        created_at=now,
    )

    _runs.append({
        "run_id": run_id,
        "description": description,
        "status": "success",
        "file_count": len(artifacts),
        "tool_call_count": len(tool_calls),
        "created_at": now,
    })

    return response


def get_history() -> list[dict]:
    return list(reversed(_runs))