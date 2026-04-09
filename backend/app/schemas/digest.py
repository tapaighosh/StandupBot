"""
StandupBot — Digest Schemas

Request/response schemas for digest views and analytics.
"""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DigestMemberEntry(BaseModel):
    """A member's entry within a digest."""

    member_id: UUID
    member_name: str
    submitted: bool
    has_blocker: bool
    answers: list[dict] = []


class DigestResponse(BaseModel):
    """Full digest response."""

    id: UUID
    team_id: UUID
    digest_date: date
    ai_summary: str | None = None
    total_members: int
    responded_count: int
    response_rate: float = Field(..., description="Response rate as percentage (0-100)")
    non_responders: list[str] = Field(default_factory=list, description="Names of non-responders")
    blockers: list[dict] = Field(default_factory=list, description="Flagged blockers")
    entries: list[DigestMemberEntry] = []
    status: str
    sent_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DigestListItem(BaseModel):
    """Summary digest for list/history views."""

    id: UUID
    digest_date: date
    total_members: int
    responded_count: int
    response_rate: float
    status: str
    sent_at: datetime | None = None

    model_config = {"from_attributes": True}


class TeamStatsResponse(BaseModel):
    """Dashboard analytics response for a team."""

    team_id: UUID
    period_days: int = 30
    average_response_rate: float
    total_standups: int
    total_blockers: int
    member_stats: list[dict] = Field(default_factory=list, description="Per-member response rates")


class BlockerTrendResponse(BaseModel):
    """Blocker frequency trends."""

    team_id: UUID
    period_days: int = 30
    total_blockers: int
    trend_data: list[dict] = Field(default_factory=list, description="Daily blocker counts")
    common_themes: list[str] = Field(default_factory=list, description="Most frequent blocker themes")
