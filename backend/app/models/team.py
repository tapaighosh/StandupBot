"""
StandupBot — Team & TeamSettings Models

Represents a team created by a manager, with configuration for
reminders, digest timing, and submission windows.
"""

import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin


class Team(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    """A team owned by a manager."""

    __tablename__ = "teams"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")

    # Schedule configuration
    reminder_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(8, 0))
    digest_time: Mapped[time] = mapped_column(Time, nullable=False, default=time(10, 0))
    submission_window_start: Mapped[time] = mapped_column(Time, nullable=False, default=time(6, 0))
    submission_window_end: Mapped[time] = mapped_column(Time, nullable=False, default=time(11, 0))
    allow_late_submissions: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Slack integration (optional)
    slack_channel_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slack_webhook_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="teams", lazy="selectin")
    members = relationship("Member", back_populates="team", lazy="selectin")
    questions = relationship("Question", back_populates="team", lazy="selectin", order_by="Question.order_index")
    settings = relationship("TeamSettings", back_populates="team", uselist=False, lazy="selectin")
    digests = relationship("Digest", back_populates="team", lazy="noload")

    def __repr__(self) -> str:
        return f"<Team id={self.id} name={self.name}>"


class TeamSettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Notification and reminder settings for a team."""

    __tablename__ = "team_settings"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), unique=True, nullable=False
    )

    email_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    slack_reminders_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nudge_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    nudge_delay_minutes: Mapped[int] = mapped_column(Integer, default=120, nullable=False)
    low_response_alert_threshold: Mapped[float] = mapped_column(default=0.5, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="settings", lazy="selectin")

    def __repr__(self) -> str:
        return f"<TeamSettings team_id={self.team_id}>"
