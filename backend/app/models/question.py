"""
StandupBot — Question Model

Customizable standup questions per team.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A customizable standup question belonging to a team."""

    __tablename__ = "questions"

    team_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(1000), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    team = relationship("Team", back_populates="questions", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Question id={self.id} order={self.order_index}>"
