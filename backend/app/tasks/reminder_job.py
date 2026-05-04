"""
StandupBot — Reminder Job

Background job that sends daily standup reminders to all active members.
Triggered by APScheduler at each team's configured reminder_time in their timezone.

RETRY STRATEGY:
- Up to 3 attempts with exponential backoff (same pattern as digest_job)
- On final failure: logs error, does NOT raise (prevents scheduler crash)

FLOW:
  APScheduler → run_reminder_job(team_id)
              → NotificationService.send_daily_reminders(team_id)
              → TokenService.generate_daily_tokens()     [generates magic links]
              → EmailService.send_reminder()              [sends email per member]
"""

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger("standupbot.tasks.reminder")

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # seconds


async def run_reminder_job(team_id: UUID) -> None:
    """
    Send daily standup reminders to all active members of a team.

    Called by APScheduler at the team's reminder_time.
    Creates its own DB session — not tied to an HTTP request.
    """
    logger.info(f"Reminder job triggered for team {team_id}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            from app.database import async_session_factory
            from app.services.notification_service import NotificationService

            async with async_session_factory() as session:
                service = NotificationService(session)
                result = await service.send_daily_reminders(team_id)
                await session.commit()
                logger.info(
                    f"Reminders sent for team {team_id}: "
                    f"sent={result['sent']} failed={result['failed']} "
                    f"skipped={result['skipped']}"
                )
                return  # Success

        except Exception as e:
            logger.error(
                f"Reminder job failed for team {team_id} "
                f"(attempt {attempt}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[attempt - 1]
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.critical(
                    f"Reminder job PERMANENTLY FAILED for team {team_id} "
                    f"after {MAX_RETRIES} attempts"
                )
                # Do NOT raise — scheduler must continue
