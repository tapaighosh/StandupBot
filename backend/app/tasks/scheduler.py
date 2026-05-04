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
    nudge_delay_minutes: int = 120,
) -> None:
    """
    Register scheduled jobs for a team.

    Called when:
    - A new team is created
    - A team's schedule settings are updated

    Creates:
    - Digest job:   triggers at digest_time in team's timezone
    - Reminder job: triggers at reminder_time in team's timezone
    - Nudge job:    triggers at reminder_time + nudge_delay_minutes in team's timezone
    """
    team_id_str = str(team_id)

    # Parse times if string (e.g., "10:00")
    def _parse(t: str | time) -> tuple[int, int]:
        if isinstance(t, str):
            parts = t.split(":")
            return int(parts[0]), int(parts[1])
        return t.hour, t.minute

    d_hour, d_minute = _parse(digest_time)
    r_hour, r_minute = _parse(reminder_time)

    # Calculate nudge time = reminder_time + nudge_delay_minutes
    total_nudge_minutes = r_hour * 60 + r_minute + nudge_delay_minutes
    n_hour = (total_nudge_minutes // 60) % 24
    n_minute = total_nudge_minutes % 60

    # Remove existing jobs for this team (idempotent update)
    remove_team_jobs(team_id_str)

    team_uuid = UUID(team_id_str) if isinstance(team_id, str) else team_id

    # ── Digest Job ──
    from app.tasks.digest_job import run_digest_job

    scheduler.add_job(
        run_digest_job,
        trigger=CronTrigger(hour=d_hour, minute=d_minute, timezone=timezone),
        id=f"digest_{team_id_str}",
        args=[team_uuid],
        name=f"Daily digest for team {team_id_str[:8]}",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # ── Reminder Job ──
    from app.tasks.reminder_job import run_reminder_job

    scheduler.add_job(
        run_reminder_job,
        trigger=CronTrigger(hour=r_hour, minute=r_minute, timezone=timezone),
        id=f"reminder_{team_id_str}",
        args=[team_uuid],
        name=f"Daily reminder for team {team_id_str[:8]}",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # ── Nudge Job ──
    from app.tasks.nudge_job import run_nudge_job

    scheduler.add_job(
        run_nudge_job,
        trigger=CronTrigger(hour=n_hour, minute=n_minute, timezone=timezone),
        id=f"nudge_{team_id_str}",
        args=[team_uuid],
        name=f"Nudge non-responders for team {team_id_str[:8]}",
        replace_existing=True,
        misfire_grace_time=300,
    )

    logger.info(
        f"Scheduled jobs for team {team_id_str[:8]}: "
        f"reminder={r_hour:02d}:{r_minute:02d} "
        f"nudge={n_hour:02d}:{n_minute:02d} "
        f"digest={d_hour:02d}:{d_minute:02d} "
        f"tz={timezone}"
    )


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

