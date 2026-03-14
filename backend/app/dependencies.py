"""
FastAPI dependency injection functions.

Provides:
- get_db: Yields an async database session
- get_current_user: Decodes JWT and returns the authenticated user (Phase 3)
"""

from app.db.database import get_db  # noqa: F401 — re-exported for convenience
