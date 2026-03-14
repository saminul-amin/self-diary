"""
Pydantic request/response schemas — shared base models.
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Error detail inside the response envelope."""

    code: str
    message: str


class MetaInfo(BaseModel):
    """Pagination / meta information."""

    page: int = 1
    page_size: int = 20
    total: int = 0


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    data: T | None = None
    meta: MetaInfo | None = None
    error: ErrorDetail | None = None

    @classmethod
    def success(cls, data: Any, meta: MetaInfo | None = None) -> "ApiResponse[Any]":
        return cls(data=data, meta=meta)

    @classmethod
    def fail(cls, code: str, message: str) -> "ApiResponse[Any]":
        return cls(error=ErrorDetail(code=code, message=message))
