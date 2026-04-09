"""
StandupBot — Teams API Routes

Team CRUD, member management, and question configuration.
Implementation stubs — full logic in Module 1.
"""

from uuid import UUID

from fastapi import APIRouter

from app.dependencies import CurrentUserId, DBSession
from app.schemas.common import MessageResponse
from app.schemas.member import MemberInviteRequest, MemberResponse
from app.schemas.team import (
    QuestionCreate,
    QuestionResponse,
    TeamCreateRequest,
    TeamListResponse,
    TeamResponse,
    TeamUpdateRequest,
)

router = APIRouter()


# ── Team CRUD ──


@router.post(
    "/",
    response_model=TeamResponse,
    status_code=201,
    summary="Create a team",
    description="Create a new team with questions and schedule configuration.",
)
async def create_team(
    request: TeamCreateRequest,
    user_id: CurrentUserId,
    db: DBSession,
) -> TeamResponse:
    """Create a new team."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Create team")


@router.get(
    "/",
    response_model=list[TeamListResponse],
    summary="List teams",
    description="Get all teams owned by the current user.",
)
async def list_teams(user_id: CurrentUserId, db: DBSession) -> list[TeamListResponse]:
    """List all teams owned by the authenticated user."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — List teams")


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team details",
    description="Get full details of a specific team.",
)
async def get_team(team_id: UUID, user_id: CurrentUserId, db: DBSession) -> TeamResponse:
    """Get team details including questions and member count."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Get team")


@router.put(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Update team",
    description="Update team settings (name, timezone, schedule).",
)
async def update_team(
    team_id: UUID,
    request: TeamUpdateRequest,
    user_id: CurrentUserId,
    db: DBSession,
) -> TeamResponse:
    """Update team settings."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Update team")


@router.delete(
    "/{team_id}",
    response_model=MessageResponse,
    summary="Delete team",
    description="Soft-delete a team and deactivate all members.",
)
async def delete_team(team_id: UUID, user_id: CurrentUserId, db: DBSession) -> MessageResponse:
    """Soft-delete a team."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Delete team")


# ── Member Management ──


@router.post(
    "/{team_id}/members",
    response_model=MemberResponse,
    status_code=201,
    summary="Invite member",
    description="Invite a new member to the team by email.",
)
async def invite_member(
    team_id: UUID,
    request: MemberInviteRequest,
    user_id: CurrentUserId,
    db: DBSession,
) -> MemberResponse:
    """Invite a member to the team."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Invite member")


@router.get(
    "/{team_id}/members",
    response_model=list[MemberResponse],
    summary="List members",
    description="List all active members of a team.",
)
async def list_members(
    team_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> list[MemberResponse]:
    """List active team members."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — List members")


@router.delete(
    "/{team_id}/members/{member_id}",
    response_model=MessageResponse,
    summary="Remove member",
    description="Deactivate (soft-remove) a team member.",
)
async def remove_member(
    team_id: UUID,
    member_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> MessageResponse:
    """Remove (deactivate) a team member."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Remove member")


# ── Question Management ──


@router.get(
    "/{team_id}/questions",
    response_model=list[QuestionResponse],
    summary="Get questions",
    description="Get all active standup questions for a team.",
)
async def get_questions(
    team_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> list[QuestionResponse]:
    """Get team's standup questions."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Get questions")


@router.put(
    "/{team_id}/questions",
    response_model=list[QuestionResponse],
    summary="Update questions",
    description="Replace all standup questions for a team.",
)
async def update_questions(
    team_id: UUID,
    questions: list[QuestionCreate],
    user_id: CurrentUserId,
    db: DBSession,
) -> list[QuestionResponse]:
    """Update team's standup questions (full replacement)."""
    # TODO: Implement in Module 1
    raise NotImplementedError("Module 1: Teams — Update questions")
