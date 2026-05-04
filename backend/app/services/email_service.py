"""
StandupBot — Email Service

Transactional email delivery via Resend API with Jinja2 HTML templates.

DESIGN PRINCIPLES:
==================
1. NEVER RAISE — every public method is wrapped in try/except.
   Email failure should NEVER crash the scheduler or digest job.
   We log errors and return False; the caller decides how to proceed.

2. JINJA2 TEMPLATES — HTML emails are rendered from templates in
   backend/app/templates/. This keeps the service clean and makes
   it easy to update email design without touching Python code.

3. PLAIN TEXT FALLBACK — Resend sends both HTML and plain text.
   This improves deliverability and supports email clients that
   block HTML.

4. GRACEFUL DEGRADATION — If RESEND_API_KEY is not set, we log
   a warning and return False. This keeps development/test
   environments working without a real email account.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings

logger = logging.getLogger("standupbot.services.email")

# ── Jinja2 Template Environment ──
# Loads templates from backend/app/templates/
_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _render(template_name: str, **ctx) -> str:
    """Render a Jinja2 template with the given context variables."""
    tmpl = _jinja_env.get_template(template_name)
    return tmpl.render(**ctx)


class EmailService:
    """
    Service for sending transactional emails via Resend.

    All public methods:
    - Accept strongly-typed parameters (no raw dict)
    - Return True on success, False on any failure
    - Log errors at ERROR level, never raise
    """

    def __init__(self) -> None:
        self._client = None
        if settings.RESEND_API_KEY:
            try:
                import resend
                resend.api_key = settings.RESEND_API_KEY
                self._client = resend
                logger.info("Resend email client initialized")
            except ImportError:
                logger.warning("resend package not installed — emails disabled")
        else:
            logger.warning("RESEND_API_KEY not set — emails will be skipped")

    def _is_ready(self) -> bool:
        """Check if email sending is configured."""
        return self._client is not None

    async def send_reminder(
        self,
        to_email: str,
        member_name: str,
        team_name: str,
        magic_link: str,
    ) -> bool:
        """
        Send a standup reminder email with the member's magic link.

        [TC-5.1.2] Reminder contains correct personalized magic link
        [TC-5.1.3] Reminder sent via email when email reminders enabled
        """
        if not self._is_ready():
            logger.info(f"[email] Skipping reminder to {to_email} — client not configured")
            return False

        try:
            html = _render(
                "reminder.html",
                member_name=member_name,
                team_name=team_name,
                magic_link=magic_link,
            )
            plain = (
                f"Hey {member_name}!\n\n"
                f"Time for your standup with {team_name}.\n"
                f"Submit here (2 mins): {magic_link}\n\n"
                "— StandupBot"
            )
            self._client.Emails.send({
                "from": settings.FROM_EMAIL,
                "to": [to_email],
                "subject": f"⚡ Your standup reminder — {team_name}",
                "html": html,
                "text": plain,
            })
            logger.info(f"[email] Reminder sent to {to_email} ({member_name})")
            return True

        except Exception as e:
            logger.error(f"[email] Failed to send reminder to {to_email}: {e}")
            return False

    async def send_nudge(
        self,
        to_email: str,
        member_name: str,
        team_name: str,
        magic_link: str,
    ) -> bool:
        """
        Send a follow-up nudge email.

        Slightly more urgent tone than the reminder.
        [TC-5.2.1] Nudge sent if no submission by T + configured delay
        """
        if not self._is_ready():
            logger.info(f"[email] Skipping nudge to {to_email} — client not configured")
            return False

        try:
            html = _render(
                "nudge.html",
                member_name=member_name,
                team_name=team_name,
                magic_link=magic_link,
            )
            plain = (
                f"Hey {member_name}, don't forget your standup!\n\n"
                f"Team: {team_name}\n"
                f"Submit here: {magic_link}\n\n"
                "— StandupBot"
            )
            self._client.Emails.send({
                "from": settings.FROM_EMAIL,
                "to": [to_email],
                "subject": f"⏰ Don't forget your standup — {team_name}",
                "html": html,
                "text": plain,
            })
            logger.info(f"[email] Nudge sent to {to_email} ({member_name})")
            return True

        except Exception as e:
            logger.error(f"[email] Failed to send nudge to {to_email}: {e}")
            return False

    async def send_digest(
        self,
        to_email: str,
        manager_name: str,
        team_name: str,
        digest_date: str,
        ai_summary: str | None,
        responded_count: int,
        total_members: int,
        response_rate: float,
        blockers: list[dict],
        non_responders: list[str],
        digest_id: str,
    ) -> bool:
        """
        Send the daily digest email to the team manager.

        [TC-4.1.7] Digest is sent via email
        """
        if not self._is_ready():
            logger.info(f"[email] Skipping digest to {to_email} — client not configured")
            return False

        try:
            # Color-code the response rate
            if response_rate >= 80:
                rate_color = "#00b894"
            elif response_rate >= 50:
                rate_color = "#fdcb6e"
            else:
                rate_color = "#ff6b6b"

            dashboard_url = f"{settings.FRONTEND_URL}/dashboard/digests/{digest_id}"

            html = _render(
                "digest.html",
                manager_name=manager_name,
                team_name=team_name,
                digest_date=digest_date,
                ai_summary=ai_summary,
                responded_count=responded_count,
                total_members=total_members,
                response_rate=round(response_rate, 1),
                rate_color=rate_color,
                blockers=blockers,
                non_responders=non_responders,
                dashboard_url=dashboard_url,
            )
            plain = (
                f"{team_name} — Daily Digest ({digest_date})\n"
                f"Response rate: {response_rate:.0f}% ({responded_count}/{total_members})\n\n"
                + (f"AI Summary:\n{ai_summary}\n\n" if ai_summary else "")
                + (f"Blockers: {len(blockers)}\n" if blockers else "No blockers.\n")
                + f"\nView full digest: {dashboard_url}"
            )
            self._client.Emails.send({
                "from": settings.FROM_EMAIL,
                "to": [to_email],
                "subject": f"📋 {team_name} standup digest — {digest_date}",
                "html": html,
                "text": plain,
            })
            logger.info(f"[email] Digest sent to manager {to_email} for team {team_name}")
            return True

        except Exception as e:
            logger.error(f"[email] Failed to send digest to {to_email}: {e}")
            return False

    async def send_low_response_alert(
        self,
        to_email: str,
        manager_name: str,
        team_name: str,
        response_rate: float,
        responded_count: int,
        total_members: int,
        threshold: float,
        non_responders: list[str],
        digest_id: str,
    ) -> bool:
        """
        Alert the manager when response rate drops below the configured threshold.

        [TC-5.3.1] Alert sent if response rate drops below threshold
        """
        if not self._is_ready():
            logger.info(f"[email] Skipping alert to {to_email} — client not configured")
            return False

        try:
            dashboard_url = f"{settings.FRONTEND_URL}/dashboard/digests/{digest_id}"
            html = _render(
                "alert.html",
                manager_name=manager_name,
                team_name=team_name,
                response_rate=round(response_rate, 1),
                responded_count=responded_count,
                total_members=total_members,
                threshold=round(threshold * 100),
                non_responders=non_responders,
                dashboard_url=dashboard_url,
            )
            plain = (
                f"⚠️ Low Response Alert — {team_name}\n\n"
                f"Today's response rate is {response_rate:.0f}% "
                f"({responded_count}/{total_members}), below your "
                f"{threshold * 100:.0f}% threshold.\n\n"
                f"View digest: {dashboard_url}"
            )
            self._client.Emails.send({
                "from": settings.FROM_EMAIL,
                "to": [to_email],
                "subject": f"⚠️ Low response alert — {team_name} ({response_rate:.0f}%)",
                "html": html,
                "text": plain,
            })
            logger.info(
                f"[email] Low response alert sent to {to_email}: "
                f"{response_rate:.0f}% (threshold: {threshold * 100:.0f}%)"
            )
            return True

        except Exception as e:
            logger.error(f"[email] Failed to send alert to {to_email}: {e}")
            return False
