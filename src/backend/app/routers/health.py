"""Health router — GET /health"""

from __future__ import annotations

import os

from fastapi import APIRouter

from ..models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check — also reports whether the API key is configured."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        api_key_configured=bool(os.environ.get("ANTHROPIC_API_KEY")),
    )