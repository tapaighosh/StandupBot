"""
StandupBot — Nudge Job

Background job that sends follow-up nudges to members who haven't submitted.
Triggered by APScheduler at reminder_time + nudge_delay_minutes in team's timezone.

NUDGE TIMING EXAMPLE:
  Team reminder_time = 09:00
  nudge_delay_minutes = 120 (2 hours)
  → Nudge job fires at 11:00

GUARD RAILS (enforced in NotificationService):
  1. nudge_enabled must be True for the team
  2. Member must NOT have submitted yet today
  3. Member must NOT have been nudged already today (nudge_sent_at is None)
  4. Member must be active
"""

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger("standupbot.tasks.nudge")

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # seconds


async def run_nudge_job(team_id: UUID) -> None:
    """
    Send follow-up nudges to non-responders for a team.

    Called by APScheduler at reminder_time + nudge_delay_minutes.
    Creates its own DB session — not tied to an HTTP request.
    """
    logger.info(f"Nudge job triggered for team {team_id}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from app.database import async_session_factory
            from app.services.notification_service import NotificationService

            async with async_session_factory() as session:
                service = NotificationService(session)
                result = await service.send_nudges(team_id)
                await session.commit()
                logger.info(
                    f"Nudges sent for team {team_id}: "
                    f"nudged={result['nudged']} "
                    f"already_submitted={result['already_submitted']} "
                    f"skipped={result['skipped']}"
                )
                return  # Success

        except Exception as e:
            logger.error(
                f"Nudge job failed for team {team_id} "
                f"(attempt {attempt}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[attempt - 1]
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.critical(
                    f"Nudge job PERMANENTLY FAILED for team {team_id} "
                    f"after {MAX_RETRIES} attempts"
                )
                # Do NOT raise — scheduler must continue
