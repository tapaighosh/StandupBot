"""
StandupBot — Digest Job

Background job that generates and sends daily digests.
Stub — implement in Module 4.
"""

import logging
from uuid import UUID

logger = logging.getLogger("standupbot.tasks.digest")


async def run_digest_job(team_id: UUID) -> None:
    """
    Generate and send the daily digest for a team.

    Flow:
    1. Get DB session
    2. Call DigestService.generate_digest(team_id)
    3. Log success/failure
    4. Retry on failure (up to 3 attempts)
    """
    logger.info(f"Digest job triggered for team {team_id}")
    # TODO: Implement in Module 4
    # from app.database import async_session_factory
    # from app.services.digest_service import DigestService
    #
    # async with async_session_factory() as session:
    #     service = DigestService(session)
    #     try:
    #         await service.generate_digest(team_id)
    #         await session.commit()
    #         logger.info(f"Digest generated for team {team_id}")
    #     except Exception as e:
    #         logger.error(f"Digest job failed for team {team_id}: {e}")
    #         await session.rollback()
