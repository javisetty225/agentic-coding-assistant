"""Pydantic request/response schemas — mirrors TypeScript types in frontend."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Requests ──────────────────────────────────────────────────────────────────

class GenerateRequest(BaseModel):
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Natural language description of the Langflow flow to generate.",
        examples=["Build a movie recommendation flow with MovieFilterComponent"],
    )
    api_key: str | None = Field(
        None,
        description="Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.",
    )


# ── Sub-models ────────────────────────────────────────────────────────────────

class ArtifactFile(BaseModel):
    filename: str
    content: str
    size: int
    file_type: Literal["json", "python", "markdown", "text"]


class ToolCall(BaseModel):
    tool: str
    input: dict
    result: str


# ── Responses ─────────────────────────────────────────────────────────────────

class GenerateResponse(BaseModel):
    run_id: str
    status: Literal["success", "error"]
    description: str
    artifacts: list[ArtifactFile]
    tool_calls: list[ToolCall]
    tool_call_count: int
    file_count: int
    duration_seconds: float
    created_at: datetime


class HistoryItem(BaseModel):
    run_id: str
    description: str
    status: str
    file_count: int
    tool_call_count: int
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int


class HealthResponse(BaseModel):
    status: str
    version: str
    api_key_configured: bool