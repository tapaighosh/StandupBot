"""
StandupBot — Nudge Job

Background job that sends follow-up nudges to non-responders.
Stub — implement in Module 5.
"""

import logging
from uuid import UUID

logger = logging.getLogger("standupbot.tasks.nudge")


async def run_nudge_job(team_id: UUID) -> None:
    """
    Send follow-up nudges to members who haven't submitted.

    Flow:
    1. Get DB session
    2. Check team settings (nudge_enabled, nudge_delay)
    3. Find non-responders for today
    4. Send nudges via NotificationService
    5. Log results
    """
    logger.info(f"Nudge job triggered for team {team_id}")
    # TODO: Implement in Module 5
