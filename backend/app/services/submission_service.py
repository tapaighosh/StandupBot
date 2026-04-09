"""
StandupBot — Submission Service

Business logic for standup form loading and submission processing.
Stub — implement in Module 3.
"""

import logging
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("standupbot.services.submission")


class SubmissionService:
    """Service for standup submissions."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def load_form(self, member_id: UUID, team_id: UUID, standup_date: date) -> dict:
        """
        Load the standup form for a member.

        Returns: { team_name, member_name, standup_date, questions, already_submitted }
        """
        # TODO: Implement in Module 3
        raise NotImplementedError

    async def submit_standup(
        self,
        member_id: UUID,
        team_id: UUID,
        standup_date: date,
        answers: list[dict],
    ) -> object:
        """
        Process a standup submission.

        Steps:
        1. Check submission window
        2. Check for existing submission (handle re-submission)
        3. Store submission and answers
        4. Return confirmation
        """
        # TODO: Implement in Module 3
        raise NotImplementedError

    async def get_submissions_for_date(self, team_id: UUID, standup_date: date) -> list:
        """Get all submissions for a team on a given date."""
        # TODO: Implement in Module 3
        raise NotImplementedError

    async def get_member_submission(
        self, member_id: UUID, team_id: UUID, standup_date: date
    ) -> object | None:
        """Get a specific member's submission for a date."""
        # TODO: Implement in Module 3
        raise NotImplementedError
