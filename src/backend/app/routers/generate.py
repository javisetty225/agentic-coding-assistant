"""
Generate router
POST /api/v1/generate                          — run the agent
GET  /api/v1/generate/{run_id}/download/{file} — download a generated artifact
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from ..models.schemas import GenerateRequest, GenerateResponse
from ..services.agent_service import run_agent

router = APIRouter()

# In-request artifact cache for downloads
_cache: dict[str, GenerateResponse] = {}


@router.post("/generate", response_model=GenerateResponse)
async def generate_flow(request: GenerateRequest) -> GenerateResponse:
    """
    Generate a Langflow flow JSON and custom Python component
    from a natural language description.
    """
    try:
        response = await run_agent(request.description, request.api_key)
        _cache[response.run_id] = response
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}") from e


@router.get("/generate/{run_id}/download/{filename}")
async def download_file(run_id: str, filename: str) -> PlainTextResponse:
    """Download a specific generated file by run_id and filename."""
    response = _cache.get(run_id)
    if not response:
        raise HTTPException(status_code=404, detail="Run not found")

    artifact = next(
        (a for a in response.artifacts if a.filename == filename), None
    )
    if not artifact:
        raise HTTPException(status_code=404, detail="File not found")

    media_map = {
        "json": "application/json",
        "python": "text/x-python",
        "markdown": "text/markdown",
    }

    return PlainTextResponse(
        content=artifact.content,
        media_type=media_map.get(artifact.file_type, "text/plain"),
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )