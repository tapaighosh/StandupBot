"""
StandupBot — Notification Service

Orchestrates reminder sending, nudge logic, and manager alerts.
Stub — implement in Module 5.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("standupbot.services.notification")


class NotificationService:
    """Service for managing all notifications (reminders, nudges, alerts)."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def send_daily_reminders(self, team_id: UUID) -> dict:
        """
        Send daily standup reminders to all active members of a team.

        Steps:
        1. Generate daily tokens for all members
        2. Build magic links
        3. Send via email and/or Slack (based on team settings)

        Returns: { sent: int, failed: int, skipped: int }
        """
        # TODO: Implement in Module 5
        raise NotImplementedError

    async def send_nudges(self, team_id: UUID) -> dict:
        """
        Send follow-up nudges to members who haven't submitted.

        Only sends if:
        - Nudges are enabled for the team
        - The configured delay has passed since reminder time
        - Member hasn't submitted yet
        - No nudge has been sent today

        Returns: { nudged: int, already_submitted: int }
        """
        # TODO: Implement in Module 5
        raise NotImplementedError

    async def check_response_rate_alert(self, team_id: UUID) -> bool:
        """
        Check if response rate is below threshold and alert manager.

        Returns: True if alert was sent.
        """
        # TODO: Implement in Module 5
        raise NotImplementedError
