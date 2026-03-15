"""
API v1 Router — Aggregates all v1 route modules.
"""

from fastapi import APIRouter

from app.api.v1 import auth, entries

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])

# Uncomment as each module is implemented:
# from app.api.v1 import tags, attachments
# api_router.include_router(tags.router,         prefix="/tags",        tags=["tags"])
# api_router.include_router(attachments.router,  prefix="/attachments", tags=["attachments"])
