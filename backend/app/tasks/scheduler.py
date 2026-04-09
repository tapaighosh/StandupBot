"""
StandupBot — APScheduler Configuration

Configures and manages the background job scheduler.
Stub — implement in Modules 4 & 5.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger("standupbot.scheduler")

# Global scheduler instance
scheduler = AsyncIOScheduler()


def start_scheduler() -> None:
    """Start the APScheduler background job scheduler."""
    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    # TODO: Register jobs in Module 4 (Digest) and Module 5 (Notifications)
    # Example:
    # from app.tasks.digest_job import run_digest_job
    # from app.tasks.reminder_job import run_reminder_job
    # from app.tasks.nudge_job import run_nudge_job
    #
    # Per-team scheduling will be done dynamically when teams are created/updated.
    # See architecture.md for the data flow.

    scheduler.start()
    logger.info("APScheduler started successfully")


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("APScheduler shut down gracefully")


def add_team_jobs(team_id: str, timezone: str, reminder_time: str, digest_time: str) -> None:
    """
    Register scheduled jobs for a team (called when team is created/updated).

    Creates:
    - Reminder job: triggers at reminder_time in team's timezone
    - Digest job: triggers at digest_time in team's timezone
    - Nudge job: triggers at reminder_time + nudge_delay

    TODO: Implement in Modules 4 & 5
    """
    logger.info(f"Team jobs registration for {team_id} — not yet implemented")


def remove_team_jobs(team_id: str) -> None:
    """Remove all scheduled jobs for a team (called when team is deleted)."""
    logger.info(f"Team jobs removal for {team_id} — not yet implemented")
