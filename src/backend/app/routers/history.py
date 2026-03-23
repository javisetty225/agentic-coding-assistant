"""History router — GET /api/v1/history"""

from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import HistoryItem, HistoryResponse
from ..services.agent_service import get_history

router = APIRouter()


@router.get("/history", response_model=HistoryResponse)
async def list_history() -> HistoryResponse:
    """Return all previous generation runs, newest first."""
    items = get_history()
    return HistoryResponse(
        items=[HistoryItem(**item) for item in items],
        total=len(items),
    )