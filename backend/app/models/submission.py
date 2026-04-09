"""
StandupBot — Submission & Answer Models

Stores standup submissions from team members.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Submission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A standup submission from a team member for a specific day."""

    __tablename__ = "submissions"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    standup_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_late: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Relationships
    member = relationship("Member", back_populates="submissions", lazy="selectin")
    answers = relationship("Answer", back_populates="submission", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Submission id={self.id} member_id={self.member_id} date={self.standup_date}>"


class Answer(UUIDPrimaryKeyMixin, Base):
    """An answer to a specific question within a submission."""

    __tablename__ = "answers"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        nullable=False,
    )

    # Relationships
    submission = relationship("Submission", back_populates="answers", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Answer id={self.id} submission_id={self.submission_id}>"
