"""
StandupBot — Digest Service

Assembles daily digests from submissions, calls LLM for summary,
and dispatches via email/Slack.
Stub — implement in Module 4.
"""

import logging
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("standupbot.services.digest")


class DigestService:
    """Service for digest generation and retrieval."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def generate_digest(self, team_id: UUID, digest_date: date | None = None) -> object:
        """
        Generate a digest for a team.

        Steps:
        1. Fetch team config and members
        2. Collect all submissions for the day
        3. Identify non-responders
        4. Flag entries with blockers
        5. Call LLM for summary (with fallback)
        6. Assemble digest object
        7. Save to DB
        8. Dispatch via email + Slack
        """
        # TODO: Implement in Module 4
        raise NotImplementedError

    async def get_todays_digest(self, team_id: UUID, owner_id: UUID) -> object | None:
        """Get today's digest for a team."""
        # TODO: Implement in Module 4
        raise NotImplementedError

    async def get_digest_history(
        self, team_id: UUID, owner_id: UUID, page: int = 1, page_size: int = 20
    ) -> list:
        """Get paginated digest history."""
        # TODO: Implement in Module 4
        raise NotImplementedError

    async def get_digest_by_id(self, team_id: UUID, digest_id: UUID, owner_id: UUID) -> object:
        """Get a specific digest by ID."""
        # TODO: Implement in Module 4
        raise NotImplementedError
