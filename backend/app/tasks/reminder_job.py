"""
StandupBot — Reminder Job

Background job that sends daily standup reminders.
Stub — implement in Module 5.
"""

import logging
from uuid import UUID

logger = logging.getLogger("standupbot.tasks.reminder")


async def run_reminder_job(team_id: UUID) -> None:
    """
    Send daily standup reminders to all active members of a team.

    Flow:
    1. Get DB session
    2. Generate daily tokens via TokenService
    3. Send reminders via NotificationService
    4. Log results
    """
    logger.info(f"Reminder job triggered for team {team_id}")
    # TODO: Implement in Module 5
