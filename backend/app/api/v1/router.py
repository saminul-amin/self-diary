"""
API v1 Router — Aggregates all v1 route modules.
"""

from fastapi import APIRouter

from app.api.v1 import attachments, auth, entries, tags

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(attachments.router, tags=["attachments"])
