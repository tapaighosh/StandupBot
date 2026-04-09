"""
StandupBot — Member Model

Represents a team member who submits standups.
Members don't have accounts — they use magic links (tokens).
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Member(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A team member who submits standups via magic links."""

    __tablename__ = "members"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="members", lazy="selectin")
    submissions = relationship("Submission", back_populates="member", lazy="noload")
    tokens = relationship("StandupToken", back_populates="member", lazy="noload")

    def __repr__(self) -> str:
        return f"<Member id={self.id} email={self.email} team_id={self.team_id}>"
