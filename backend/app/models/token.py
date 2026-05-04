"""
StandupBot — StandupToken Model

Time-scoped magic link tokens for member standup submissions.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class StandupToken(UUIDPrimaryKeyMixin, Base):
    """A time-scoped token that grants a member access to submit a standup."""

    __tablename__ = "standup_tokens"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    standup_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    nudge_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    member = relationship("Member", back_populates="tokens", lazy="selectin")

    def __repr__(self) -> str:
        return f"<StandupToken id={self.id} member_id={self.member_id} date={self.standup_date}>"
