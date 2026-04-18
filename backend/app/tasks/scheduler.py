"""
StandupBot — APScheduler Configuration

Configures and manages the background job scheduler.

SCHEDULING MODEL:
=================

Each team gets its own set of scheduled jobs:
- digest_job: runs at team's digest_time in team's timezone
- reminder_job: runs at team's reminder_time (Module 5)
- nudge_job: runs at reminder_time + nudge_delay (Module 5)

Jobs are identified by: "{type}_{team_id}" (e.g., "digest_abc123")
This makes it easy to add/update/remove jobs per team.

WHY APSCHEDULER (not Celery)?
- No separate broker (Redis/RabbitMQ) needed
- Runs in-process with the FastAPI app
- Built-in timezone handling via CronTrigger
- Sufficient for our scale (< 1000 teams in MVP)
"""

import logging
from datetime import time
from uuid import UUID

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("standupbot.scheduler")

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Start the APScheduler background job scheduler."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    scheduler.start()
    logger.info("APScheduler started successfully")


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shut down gracefully")


def add_team_jobs(
    team_id: str | UUID,
    timezone: str,
    reminder_time: str | time,
    digest_time: str | time,
) -> None:
    """
    Register scheduled jobs for a team.

    Called when:
    - A new team is created
    - A team's schedule settings are updated

    Creates:
    - Digest job: triggers at digest_time in team's timezone

    Reminder + nudge jobs will be added in Module 5.
    """
    team_id_str = str(team_id)

    # Parse time if string (e.g., "10:00")
    if isinstance(digest_time, str):
        parts = digest_time.split(":")
        d_hour, d_minute = int(parts[0]), int(parts[1])
    else:
        d_hour, d_minute = digest_time.hour, digest_time.minute

    # Remove existing jobs for this team (idempotent update)
    remove_team_jobs(team_id_str)

    # ── Digest Job ──
    from app.tasks.digest_job import run_digest_job

    digest_job_id = f"digest_{team_id_str}"
    scheduler.add_job(
        run_digest_job,
        trigger=CronTrigger(
            hour=d_hour,
            minute=d_minute,
            timezone=timezone,
        ),
        id=digest_job_id,
        args=[UUID(team_id_str) if isinstance(team_id, str) else team_id],
        name=f"Daily digest for team {team_id_str[:8]}",
        replace_existing=True,
        misfire_grace_time=300,  # 5 min grace period if missed
    )

    logger.info(
        f"Scheduled digest job for team {team_id_str[:8]}: "
        f"{d_hour:02d}:{d_minute:02d} {timezone}"
    )

    # TODO (Module 5): Add reminder_job and nudge_job here


def remove_team_jobs(team_id: str | UUID) -> None:
    """Remove all scheduled jobs for a team (called when team is deleted)."""
    team_id_str = str(team_id)
    job_prefixes = ["digest_", "reminder_", "nudge_"]

    for prefix in job_prefixes:
        job_id = f"{prefix}{team_id_str}"
        try:
            scheduler.remove_job(job_id)
            logger.info(f"Removed job {job_id}")
        except Exception:
            pass  # Job didn't exist — that's fine
