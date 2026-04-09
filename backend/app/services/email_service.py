"""
StandupBot — Email Service

Transactional email delivery via Resend.
Stub — implement in Module 5.
"""

import logging

from app.config import settings
from app.exceptions import ExternalServiceError

logger = logging.getLogger("standupbot.services.email")


class EmailService:
    """Service for sending transactional emails via Resend."""

    async def send_reminder(self, to_email: str, member_name: str, magic_link: str) -> bool:
        """
        Send a standup reminder email to a team member.

        Returns: True if sent successfully, False otherwise.
        """
        # TODO: Implement in Module 5
        logger.info(f"Reminder email to {to_email} — not yet implemented")
        return False

    async def send_digest(
        self, to_email: str, manager_name: str, team_name: str, digest_html: str
    ) -> bool:
        """
        Send a digest email to the manager.

        Returns: True if sent successfully, False otherwise.
        """
        # TODO: Implement in Module 4/5
        logger.info(f"Digest email to {to_email} — not yet implemented")
        return False

    async def send_nudge(self, to_email: str, member_name: str, magic_link: str) -> bool:
        """
        Send a follow-up nudge email to a non-responding member.

        Returns: True if sent successfully, False otherwise.
        """
        # TODO: Implement in Module 5
        logger.info(f"Nudge email to {to_email} — not yet implemented")
        return False

    async def send_low_response_alert(
        self, to_email: str, manager_name: str, team_name: str, response_rate: float
    ) -> bool:
        """
        Alert manager when response rate drops below threshold.

        Returns: True if sent successfully, False otherwise.
        """
        # TODO: Implement in Module 5
        logger.info(f"Low response alert to {to_email} — not yet implemented")
        return False
