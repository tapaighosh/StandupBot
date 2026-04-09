"""
StandupBot — Member Schemas

Request/response schemas for member management.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class MemberInviteRequest(BaseModel):
    """Request body for inviting a member to a team."""

    email: EmailStr = Field(..., description="Member's email address")
    name: str = Field(..., min_length=1, max_length=255, description="Member's display name")


class MemberResponse(BaseModel):
    """Member detail response."""

    id: UUID
    email: str
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MemberUpdateRequest(BaseModel):
    """Request body for updating member info."""

    name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None
