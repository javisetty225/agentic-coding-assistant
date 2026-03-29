"""
Agentic Coding Assistant — FastAPI Backend
REST API microservice wrapping the Langflow agent.

Uvicorn entry points:
  Factory:   uvicorn src.backend.app.main:create_app --factory
  Singleton: uvicorn src.backend.app.main:app
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.app.routers import generate, health, history


def create_app() -> FastAPI:
    """Application factory — used by Dockerfile CMD --factory flag."""
    application = FastAPI(
        title="Agentic Coding Assistant API",
        description=(
            "REST API for generating Langflow flows and custom Python "
            "components from a natural language description."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",   # Vite dev server
            "http://localhost:3000",   # CRA fallback
            "http://localhost:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router, tags=["Health"])
    application.include_router(generate.router, prefix="/api/v1", tags=["Generate"])
    application.include_router(history.router, prefix="/api/v1", tags=["History"])

    return application


# Singleton instance for direct uvicorn usage
app = create_app()