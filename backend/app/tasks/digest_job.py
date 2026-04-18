"""
StandupBot — Digest Job

Background job that generates daily digests for teams.
Triggered by APScheduler at each team's configured digest_time.

RETRY STRATEGY:
- Up to 3 attempts with exponential backoff
- Each retry gets a fresh DB session
- On final failure: logs error, does NOT raise (prevents scheduler crash)

WHY ASYNC?
- The LLM call can take 2-5 seconds
- We don't want to block the scheduler's event loop
- Each team's digest runs independently
"""

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger("standupbot.tasks.digest")

MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 10]  # seconds between retries


async def run_digest_job(team_id: UUID) -> None:
    """
    Generate and save the daily digest for a team.

    This function is called by APScheduler at the team's digest_time.
    It creates its own DB session (not tied to an HTTP request).
    """
    logger.info(f"Digest job triggered for team {team_id}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Import here to avoid circular imports at module level
            from app.database import async_session_factory
            from app.services.digest_service import DigestService

            async with async_session_factory() as session:
                service = DigestService(session)
                digest = await service.generate_digest(team_id)
                await session.commit()
                logger.info(
                    f"Digest generated successfully for team {team_id}: "
                    f"responded={digest.responded_count}/{digest.total_members}"
                )
                return  # Success — exit retry loop

        except Exception as e:
            logger.error(
                f"Digest job failed for team {team_id} "
                f"(attempt {attempt}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[attempt - 1]
                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
            else:
                logger.critical(
                    f"Digest job PERMANENTLY FAILED for team {team_id} "
                    f"after {MAX_RETRIES} attempts"
                )
                # Do NOT raise — APScheduler should continue running other jobs
