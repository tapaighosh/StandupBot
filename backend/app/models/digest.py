"""
StandupBot — Digest & DigestEntry Models

Stores daily digest summaries assembled from submissions.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Digest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A daily digest assembled from team submissions and sent to the manager."""

    __tablename__ = "digests"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    digest_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    ai_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_members: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    responded_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    non_responders: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    blockers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, sent, failed
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    team = relationship("Team", back_populates="digests", lazy="selectin")
    entries = relationship("DigestEntry", back_populates="digest", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Digest id={self.id} team_id={self.team_id} date={self.digest_date}>"


class DigestEntry(UUIDPrimaryKeyMixin, Base):
    """An individual entry within a digest, linking a member's submission."""

    __tablename__ = "digest_entries"

    digest_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("digests.id"), nullable=False, index=True
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id"), nullable=False
    )
    submission_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=True
    )
    has_blocker: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    digest = relationship("Digest", back_populates="entries", lazy="selectin")

    def __repr__(self) -> str:
        return f"<DigestEntry digest_id={self.digest_id} member_id={self.member_id}>"
