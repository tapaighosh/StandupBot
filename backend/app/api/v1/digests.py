"""
StandupBot — Digests API Routes

Endpoints for digest retrieval and manual trigger.
Implementation stubs — full logic in Module 4.
"""

from uuid import UUID

from fastapi import APIRouter, Query

from app.dependencies import CurrentUserId, DBSession
from app.schemas.common import MessageResponse
from app.schemas.digest import DigestListItem, DigestResponse

router = APIRouter()


@router.get(
    "/{team_id}/today",
    response_model=DigestResponse | None,
    summary="Get today's digest",
    description="Retrieve today's digest for a team, if it exists.",
)
async def get_todays_digest(
    team_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> DigestResponse | None:
    """Get today's digest for a team."""
    # TODO: Implement in Module 4
    raise NotImplementedError("Module 4: Digests — Get today's digest")


@router.get(
    "/{team_id}/history",
    response_model=list[DigestListItem],
    summary="Get digest history",
    description="Retrieve paginated digest history for a team.",
)
async def get_digest_history(
    team_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> list[DigestListItem]:
    """Get paginated digest history."""
    # TODO: Implement in Module 4
    raise NotImplementedError("Module 4: Digests — Get history")


@router.get(
    "/{team_id}/{digest_id}",
    response_model=DigestResponse,
    summary="Get specific digest",
    description="Retrieve a specific digest by ID.",
)
async def get_digest(
    team_id: UUID,
    digest_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> DigestResponse:
    """Get a specific digest."""
    # TODO: Implement in Module 4
    raise NotImplementedError("Module 4: Digests — Get digest")


@router.post(
    "/{team_id}/trigger",
    response_model=MessageResponse,
    summary="Manually trigger digest",
    description="Manually trigger digest generation for a team.",
)
async def trigger_digest(
    team_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> MessageResponse:
    """Manually trigger digest generation."""
    # TODO: Implement in Module 4
    raise NotImplementedError("Module 4: Digests — Trigger digest")
