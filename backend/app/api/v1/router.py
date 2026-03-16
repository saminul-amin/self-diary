"""
API v1 Router — Aggregates all v1 route modules.
"""

from fastapi import APIRouter

from app.api.v1 import auth, entries, tags

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])

# Uncomment as each module is implemented:
# from app.api.v1 import attachments
# api_router.include_router(attachments.router,  prefix="/attachments", tags=["attachments"])
