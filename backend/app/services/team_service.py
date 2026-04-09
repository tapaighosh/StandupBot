"""
StandupBot — Team Service

Business logic for team CRUD, member management, and question configuration.
Stub — implement in Module 1.
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("standupbot.services.team")


class TeamService:
    """Service for team and member management."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_team(self, owner_id: UUID, data: dict) -> object:
        """Create a new team with default questions and settings."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def list_teams(self, owner_id: UUID) -> list:
        """List all teams owned by a user."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def get_team(self, team_id: UUID, owner_id: UUID) -> object:
        """Get team by ID, verifying ownership."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def update_team(self, team_id: UUID, owner_id: UUID, data: dict) -> object:
        """Update team settings."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def delete_team(self, team_id: UUID, owner_id: UUID) -> None:
        """Soft-delete a team."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def invite_member(self, team_id: UUID, owner_id: UUID, data: dict) -> object:
        """Invite a member to the team."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def list_members(self, team_id: UUID, owner_id: UUID) -> list:
        """List active team members."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def remove_member(self, team_id: UUID, member_id: UUID, owner_id: UUID) -> None:
        """Deactivate a team member."""
        # TODO: Implement in Module 1
        raise NotImplementedError

    async def update_questions(self, team_id: UUID, owner_id: UUID, questions: list) -> list:
        """Replace all questions for a team."""
        # TODO: Implement in Module 1
        raise NotImplementedError
