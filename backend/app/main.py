"""
SelfDiary — FastAPI Application Entry Point.

This module creates and configures the FastAPI application instance,
including middleware, exception handlers, and route registration.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import register_middleware
from app.db.database import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    setup_logging()
    logger.info(
        "Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.environment
    )
    yield
    # Shutdown: dispose engine connection pool
    await engine.dispose()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        description="Personal diary REST API",
        version=settings.app_version,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
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

    # ── Custom middleware ──
    register_middleware(app)

    # ── Exception handlers ──
    register_exception_handlers(app)

    # ── Health check ──
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}

    # ── API v1 routes ──
    from app.api.v1.router import api_router

    app.include_router(api_router, prefix="/v1")

    return app


app = create_app()
