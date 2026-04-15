"""
StandupBot — Teams API Routes

Team CRUD, member management, and question configuration.

ROUTE PATTERN:
  Every route follows the same structure:
  1. Parse request (FastAPI does this automatically via Pydantic)
  2. Create service instance with the DB session
  3. Call the service method (the service handles ALL business logic)
  4. Format and return the response

  Routes are THIN — no business logic here. This makes the service
  layer testable independently of HTTP/FastAPI.

AUTHORIZATION:
  All routes require authentication (CurrentUserId dependency).
  The service layer then checks ownership of the specific team.
  So we have TWO layers of protection:
  1. JWT validation → "is this a logged-in user?"
  2. Team ownership → "does this user own this team?"
"""

import logging
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
from app.services.team_service import TeamService

logger = logging.getLogger("standupbot.api.teams")

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════
# TEAM CRUD
# ═══════════════════════════════════════════════════════════════════════


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
    """
    Create a new team.

    THE FLOW:
    1. Validate request body (Pydantic does this automatically)
    2. Check plan limits (free: 1 team max)
    3. Create team + 3 default questions + settings in one transaction
    4. Return the full team response with questions

    PLAN LIMIT: If the user already has the max number of teams
    for their plan, the service raises PlanLimitError (403).
    """
    service = TeamService(db)
    team = await service.create_team(owner_id=user_id, data=request)

    return TeamResponse(
        id=team.id,
        name=team.name,
        timezone=team.timezone,
        reminder_time=team.reminder_time,
        digest_time=team.digest_time,
        submission_window_start=team.submission_window_start,
        submission_window_end=team.submission_window_end,
        allow_late_submissions=team.allow_late_submissions,
        is_active=team.is_active,
        member_count=len([m for m in team.members if m.is_active]),
        questions=[QuestionResponse.model_validate(q) for q in team.questions if q.is_active],
        created_at=team.created_at,
    )


@router.get(
    "/",
    response_model=list[TeamListResponse],
    summary="List teams",
    description="Get all teams owned by the current user.",
)
async def list_teams(user_id: CurrentUserId, db: DBSession) -> list[TeamListResponse]:
    """
    List all teams owned by the authenticated user.

    Returns a summary view (no questions or settings) for quick loading.
    The frontend calls GET /{team_id} for full details when needed.
    """
    service = TeamService(db)
    teams = await service.list_teams(owner_id=user_id)

    return [
        TeamListResponse(
            id=t.id,
            name=t.name,
            timezone=t.timezone,
            member_count=len([m for m in t.members if m.is_active]),
            is_active=t.is_active,
            created_at=t.created_at,
        )
        for t in teams
    ]


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="Get team details",
    description="Get full details of a specific team.",
)
async def get_team(team_id: UUID, user_id: CurrentUserId, db: DBSession) -> TeamResponse:
    """
    Get team details including questions and member count.

    The service verifies ownership — a user can only see their own teams.
    """
    service = TeamService(db)
    team = await service.get_team(team_id=team_id, owner_id=user_id)

    return TeamResponse(
        id=team.id,
        name=team.name,
        timezone=team.timezone,
        reminder_time=team.reminder_time,
        digest_time=team.digest_time,
        submission_window_start=team.submission_window_start,
        submission_window_end=team.submission_window_end,
        allow_late_submissions=team.allow_late_submissions,
        is_active=team.is_active,
        member_count=len([m for m in team.members if m.is_active]),
        questions=[QuestionResponse.model_validate(q) for q in team.questions if q.is_active],
        created_at=team.created_at,
    )


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
    """
    Update team settings. Only the fields provided are updated (partial update).
    """
    service = TeamService(db)
    team = await service.update_team(team_id=team_id, owner_id=user_id, data=request)

    return TeamResponse(
        id=team.id,
        name=team.name,
        timezone=team.timezone,
        reminder_time=team.reminder_time,
        digest_time=team.digest_time,
        submission_window_start=team.submission_window_start,
        submission_window_end=team.submission_window_end,
        allow_late_submissions=team.allow_late_submissions,
        is_active=team.is_active,
        member_count=len([m for m in team.members if m.is_active]),
        questions=[QuestionResponse.model_validate(q) for q in team.questions if q.is_active],
        created_at=team.created_at,
    )


@router.delete(
    "/{team_id}",
    response_model=MessageResponse,
    summary="Delete team",
    description="Soft-delete a team and deactivate all members.",
)
async def delete_team(team_id: UUID, user_id: CurrentUserId, db: DBSession) -> MessageResponse:
    """
    Soft-delete a team. Sets deleted_at and deactivates all members.
    The team's data is preserved for audit purposes.
    """
    service = TeamService(db)
    await service.delete_team(team_id=team_id, owner_id=user_id)
    return MessageResponse(message="Team deleted successfully")


# ═══════════════════════════════════════════════════════════════════════
# MEMBER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════


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
    """
    Invite a member to the team.

    WHAT HAPPENS:
    - Creates a Member row in the DB (linked to the team)
    - Does NOT send an email yet (that's Module 5: Notifications)
    - The member will receive daily magic links once reminders are configured
    """
    service = TeamService(db)
    member = await service.invite_member(
        team_id=team_id,
        owner_id=user_id,
        email=request.email,
        name=request.name,
    )
    return MemberResponse.model_validate(member)


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
    """
    List active team members. Removed members are hidden.
    """
    service = TeamService(db)
    members = await service.list_members(team_id=team_id, owner_id=user_id)
    return [MemberResponse.model_validate(m) for m in members]


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
    """
    Remove a member from the team (soft-delete: sets is_active=False).
    """
    service = TeamService(db)
    await service.remove_member(team_id=team_id, member_id=member_id, owner_id=user_id)
    return MessageResponse(message="Member removed successfully")


# ═══════════════════════════════════════════════════════════════════════
# QUESTION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════


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
    """
    Get the team's active standup questions, ordered by order_index.
    """
    service = TeamService(db)
    team = await service.get_team(team_id=team_id, owner_id=user_id)
    return [
        QuestionResponse.model_validate(q)
        for q in team.questions
        if q.is_active
    ]


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
    """
    Replace all standup questions (full replacement strategy).
    Old questions are deactivated, new ones are created.
    """
    service = TeamService(db)
    new_questions = await service.update_questions(
        team_id=team_id, owner_id=user_id, questions=questions
    )
    return [QuestionResponse.model_validate(q) for q in new_questions]
