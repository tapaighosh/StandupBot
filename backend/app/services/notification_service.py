"""
StandupBot — Notification Service

Orchestrates all outbound notifications:
- Daily reminder emails/Slack DMs to team members
- Nudges to non-responders after a configurable delay
- Low response rate alerts to the manager

ORCHESTRATION PATTERN:
======================
This service is the "coordinator" — it doesn't know HOW to send emails
(that's EmailService's job) or HOW to generate tokens (TokenService).
It orchestrates them in the right order with the right business logic.

NUDGE TRACKING:
===============
The nudge system needs to ensure ONE nudge per member per day.
We track this via the StandupToken's `nudge_sent_at` field:
- If nudge_sent_at is None → not nudged yet today
- If nudge_sent_at is set → already nudged, skip
"""

import logging
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import NotFoundError
from app.models.member import Member
from app.models.submission import Submission
from app.models.team import Team
from app.models.token import StandupToken
from app.services.email_service import EmailService
from app.services.token_service import TokenService

logger = logging.getLogger("standupbot.services.notification")


class NotificationService:
    """
    Service for managing all notifications (reminders, nudges, alerts).

    Injected with an EmailService and TokenService.
    In tests, both can be replaced with mocks.
    """

    def __init__(
        self,
        db: AsyncSession,
        email_service: EmailService | None = None,
        token_service: TokenService | None = None,
    ) -> None:
        self.db = db
        self._email = email_service or EmailService()
        self._token = token_service or TokenService(db)

    # ─────────────────────────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────────────────────────

    async def _get_team(self, team_id: UUID) -> Team:
        """Load team with owner, members, and settings."""
        stmt = (
            select(Team)
            .options(
                selectinload(Team.members),
                selectinload(Team.owner),
                selectinload(Team.settings),
            )
            .where(Team.id == team_id, Team.deleted_at.is_(None), Team.is_active.is_(True))
        )
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundError(resource="Team")
        return team

    async def _has_submitted_today(self, member_id: UUID, team_id: UUID) -> bool:
        """Check if a member has already submitted their standup today."""
        today = date.today()
        stmt = select(Submission).where(
            Submission.member_id == member_id,
            Submission.team_id == team_id,
            Submission.standup_date == today,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def _get_todays_token(self, member_id: UUID) -> StandupToken | None:
        """Get today's token record for a member (if it exists)."""
        today = date.today()
        stmt = select(StandupToken).where(
            StandupToken.member_id == member_id,
            StandupToken.standup_date == today,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ─────────────────────────────────────────────────────────────────
    # 1. DAILY REMINDERS
    # ─────────────────────────────────────────────────────────────────

    async def send_daily_reminders(self, team_id: UUID) -> dict:
        """
        Send daily standup reminders to all active members of a team.

        Steps:
        1. Load team + settings
        2. Generate daily tokens for all active members
        3. Send reminder via email (if email_reminders_enabled)
        4. (Module 5b) Send via Slack DM if slack_reminders_enabled

        Returns: { sent: int, failed: int, skipped: int }

        [TC-5.1.1] Reminder sent at configured time per team timezone
        [TC-5.1.2] Reminder contains correct personalized magic link
        [TC-5.1.3] Reminder sent via email when email reminders enabled
        [TC-5.1.5] No reminder sent to inactive members
        """
        team = await self._get_team(team_id)
        settings_obj = team.settings
        sent = failed = skipped = 0

        # Generate tokens for all active members
        try:
            tokens = await self._token.generate_daily_tokens(team_id)
        except Exception as e:
            logger.error(f"[notification] Failed to generate tokens for team {team_id}: {e}")
            return {"sent": 0, "failed": 0, "skipped": len(team.members)}

        for token_data in tokens:
            member_email = token_data["email"]
            member_name = token_data["name"]
            magic_link = token_data["magic_link"]

            # Email reminders
            if settings_obj and settings_obj.email_reminders_enabled:
                ok = await self._email.send_reminder(
                    to_email=member_email,
                    member_name=member_name,
                    team_name=team.name,
                    magic_link=magic_link,
                )
                if ok:
                    sent += 1
                else:
                    failed += 1
            else:
                skipped += 1
                logger.debug(f"[notification] Email reminders disabled for team {team_id}")

            # TODO (Module 5b): Slack DM
            # if settings_obj and settings_obj.slack_reminders_enabled:
            #     await self._slack.send_reminder_dm(member_email, magic_link)

        logger.info(
            f"[notification] Reminders for team {team_id[:8] if isinstance(team_id, str) else str(team_id)[:8]}: "
            f"sent={sent} failed={failed} skipped={skipped}"
        )
        return {"sent": sent, "failed": failed, "skipped": skipped}

    # ─────────────────────────────────────────────────────────────────
    # 2. NUDGES
    # ─────────────────────────────────────────────────────────────────

    async def send_nudges(self, team_id: UUID) -> dict:
        """
        Send follow-up nudges to members who haven't submitted.

        Guards:
        - Only if nudge_enabled = True in team settings
        - Only to members who have NOT submitted today
        - Only ONE nudge per member per day (tracked via nudge_sent_at)

        Returns: { nudged: int, already_submitted: int, skipped: int }

        [TC-5.2.1] Nudge sent if no submission by T + configured delay
        [TC-5.2.2] No nudge sent if already submitted
        [TC-5.2.3] No nudge sent if nudges disabled for team
        [TC-5.2.4] Only one nudge per member per day
        """
        team = await self._get_team(team_id)
        settings_obj = team.settings
        nudged = already_submitted = skipped = 0

        # Guard: nudges disabled
        if not settings_obj or not settings_obj.nudge_enabled:
            logger.info(f"[notification] Nudges disabled for team {team_id}")
            return {"nudged": 0, "already_submitted": 0, "skipped": len(team.members)}

        for member in team.members:
            if not member.is_active:
                skipped += 1
                continue

            # Guard: already submitted
            if await self._has_submitted_today(member.id, team_id):
                already_submitted += 1
                continue

            # Guard: already nudged today
            token_record = await self._get_todays_token(member.id)
            if token_record and token_record.nudge_sent_at is not None:
                logger.debug(f"[notification] Already nudged {member.email} today")
                skipped += 1
                continue

            # Get the magic link (re-use today's token)
            if token_record:
                # Re-generate the raw token string from the token hash isn't possible;
                # so we generate a fresh one (idempotent — returns existing JWT)
                pass

            try:
                token_str = await self._token.generate_token(
                    member_id=member.id,
                    team_id=team_id,
                    standup_date=date.today(),
                )
                magic_link = f"{settings_obj.team.owner.email}"  # fallback
                from app.config import settings as app_settings
                magic_link = f"{app_settings.FRONTEND_URL}/standup/{token_str}"
            except Exception as e:
                logger.error(f"[notification] Token gen failed for nudge to {member.email}: {e}")
                skipped += 1
                continue

            ok = await self._email.send_nudge(
                to_email=member.email,
                member_name=member.name,
                team_name=team.name,
                magic_link=magic_link,
            )

            if ok:
                # Mark nudge sent on the token record
                fresh_token_record = await self._get_todays_token(member.id)
                if fresh_token_record:
                    fresh_token_record.nudge_sent_at = datetime.now(timezone.utc)
                    await self.db.flush()
                nudged += 1
            else:
                skipped += 1

        logger.info(
            f"[notification] Nudges for team {team_id}: "
            f"nudged={nudged} already_submitted={already_submitted} skipped={skipped}"
        )
        return {"nudged": nudged, "already_submitted": already_submitted, "skipped": skipped}

    # ─────────────────────────────────────────────────────────────────
    # 3. LOW RESPONSE RATE ALERT
    # ─────────────────────────────────────────────────────────────────

    async def check_response_rate_alert(self, team_id: UUID) -> bool:
        """
        Calculate today's response rate and alert the manager if below threshold.

        [TC-5.3.1] Alert sent if response rate drops below threshold
        [TC-5.3.2] No alert if response rate is above threshold

        Returns: True if alert was sent.
        """
        team = await self._get_team(team_id)
        settings_obj = team.settings
        threshold = settings_obj.low_response_alert_threshold if settings_obj else 0.5

        active_members = [m for m in team.members if m.is_active]
        total = len(active_members)
        if total == 0:
            return False

        # Count today's submissions
        today = date.today()
        stmt = select(Submission).where(
            Submission.team_id == team_id,
            Submission.standup_date == today,
        )
        result = await self.db.execute(stmt)
        submissions = result.scalars().all()
        responded_count = len(submissions)
        response_rate = (responded_count / total) * 100

        # [TC-5.3.2] No alert if above threshold
        if response_rate >= threshold * 100:
            logger.info(
                f"[notification] Response rate {response_rate:.0f}% >= "
                f"threshold {threshold * 100:.0f}% for team {team_id} — no alert"
            )
            return False

        # Identify non-responders
        submitted_member_ids = {s.member_id for s in submissions}
        non_responders = [
            m.name for m in active_members if m.id not in submitted_member_ids
        ]

        # Get today's digest ID if it exists (for the dashboard link)
        from app.models.digest import Digest
        digest_stmt = select(Digest).where(
            Digest.team_id == team_id,
            Digest.digest_date == today,
        )
        digest_result = await self.db.execute(digest_stmt)
        digest = digest_result.scalar_one_or_none()
        digest_id = str(digest.id) if digest else "today"

        manager = team.owner
        ok = await self._email.send_low_response_alert(
            to_email=manager.email,
            manager_name=manager.name,
            team_name=team.name,
            response_rate=response_rate,
            responded_count=responded_count,
            total_members=total,
            threshold=threshold,
            non_responders=non_responders,
            digest_id=digest_id,
        )

        if ok:
            logger.info(
                f"[notification] Low response alert sent for team {team_id}: "
                f"{response_rate:.0f}% < {threshold * 100:.0f}%"
            )
        return ok
