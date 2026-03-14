"""
SelfDiary — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance,
including middleware, exception handlers, and route registration.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup: initialize DB pool, create S3 bucket, etc.
    yield
    # Shutdown: close DB pool, cleanup resources


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="SelfDiary API",
        description="Personal diary REST API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health check ──
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    # ── API routes (uncomment as implemented) ──
    # from app.api.v1.router import api_router
    # app.include_router(api_router, prefix="/v1")

    return app


app = create_app()
