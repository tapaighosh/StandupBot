"""
StandupBot — Billing Service

Stripe integration for subscription management.
Stub — implement in Module 7.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import PlanLimitError

logger = logging.getLogger("standupbot.services.billing")

# Plan limits as defined in BRD
PLAN_LIMITS = {
    "free": {"max_teams": 1, "max_members": 5, "history_days": 14, "analytics": False, "slack": False},
    "starter": {"max_teams": 1, "max_members": 15, "history_days": None, "analytics": False, "slack": False},
    "growth": {"max_teams": 5, "max_members": 50, "history_days": None, "analytics": True, "slack": True},
}


class BillingService:
    """Service for Stripe billing and plan enforcement."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_plan(self, user_id: UUID) -> str:
        """Get the current plan for a user."""
        # TODO: Implement in Module 7
        return "free"

    async def check_team_limit(self, user_id: UUID) -> bool:
        """Check if user can create another team based on their plan."""
        # TODO: Implement in Module 7
        raise NotImplementedError

    async def check_member_limit(self, user_id: UUID, team_id: UUID) -> bool:
        """Check if team can add another member based on the plan."""
        # TODO: Implement in Module 7
        raise NotImplementedError

    async def create_checkout_session(self, user_id: UUID, plan: str) -> str:
        """
        Create a Stripe checkout session for plan upgrade.

        Returns: Stripe checkout URL.
        """
        # TODO: Implement in Module 7
        raise NotImplementedError

    async def handle_webhook(self, payload: bytes, signature: str) -> None:
        """Process Stripe webhook events."""
        # TODO: Implement in Module 7
        raise NotImplementedError

    async def cancel_subscription(self, user_id: UUID) -> None:
        """Cancel a user's subscription (downgrades to free)."""
        # TODO: Implement in Module 7
        raise NotImplementedError
