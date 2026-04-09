"""
StandupBot — Common Schemas

Shared Pydantic models used across all modules.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error response returned by all API endpoints."""

    detail: str = Field(..., description="Human-readable error message")
    code: str = Field(..., description="Machine-readable error code")

    model_config = {"json_schema_extra": {"examples": [{"detail": "Resource not found", "code": "NOT_FOUND"}]}}


class PaginationParams(BaseModel):
    """Query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    """Wrapper for paginated list responses."""

    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
    environment: str = "development"
    timestamp: datetime


class MessageResponse(BaseModel):
    """Simple success message response."""

    message: str
