"""
StandupBot — Team Schemas

Request/response schemas for team and question management.
"""

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionCreate(BaseModel):
    """Schema for creating a standup question."""

    text: str = Field(..., min_length=1, max_length=1000, description="Question text")
    order_index: int = Field(default=0, ge=0, description="Display order")


class QuestionResponse(BaseModel):
    """Schema for a standup question response."""

    id: UUID
    text: str
    order_index: int
    is_active: bool

    model_config = {"from_attributes": True}


class TeamCreateRequest(BaseModel):
    """Request body for creating a new team."""

    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    timezone: str = Field(default="UTC", max_length=50, description="IANA timezone")
    reminder_time: time = Field(default=time(8, 0), description="Daily reminder time")
    digest_time: time = Field(default=time(10, 0), description="Daily digest send time")
    submission_window_start: time = Field(default=time(6, 0), description="Submission window opens")
    submission_window_end: time = Field(default=time(11, 0), description="Submission window closes")
    allow_late_submissions: bool = Field(default=True, description="Allow submissions after window")
    questions: list[QuestionCreate] = Field(
        default_factory=lambda: [
            QuestionCreate(text="What did you accomplish yesterday?", order_index=0),
            QuestionCreate(text="What are you working on today?", order_index=1),
            QuestionCreate(text="Any blockers or help needed?", order_index=2),
        ],
        description="Standup questions (defaults to standard 3)",
    )


class TeamUpdateRequest(BaseModel):
    """Request body for updating team settings."""

    name: str | None = Field(None, min_length=1, max_length=255)
    timezone: str | None = Field(None, max_length=50)
    reminder_time: time | None = None
    digest_time: time | None = None
    submission_window_start: time | None = None
    submission_window_end: time | None = None
    allow_late_submissions: bool | None = None


class TeamResponse(BaseModel):
    """Team detail response."""

    id: UUID
    name: str
    timezone: str
    reminder_time: time
    digest_time: time
    submission_window_start: time
    submission_window_end: time
    allow_late_submissions: bool
    is_active: bool
    member_count: int = 0
    questions: list[QuestionResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class TeamListResponse(BaseModel):
    """Summary team response for list endpoints."""

    id: UUID
    name: str
    timezone: str
    member_count: int = 0
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
