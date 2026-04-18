"""
StandupBot — Digests API Routes

Endpoints for digest retrieval and manual trigger.
All endpoints require authentication (JWT) and team ownership.

ROUTE MAP:
  GET  /{team_id}/today     — Get today's digest
  GET  /{team_id}/history   — Get paginated digest history
  GET  /{team_id}/{digest_id} — Get specific digest
  POST /{team_id}/trigger   — Manually trigger digest generation
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Query

from app.dependencies import CurrentUserId, DBSession
from app.schemas.common import MessageResponse
from app.schemas.digest import DigestListItem, DigestResponse
from app.services.digest_service import DigestService
from app.utils.helpers import format_response_rate

logger = logging.getLogger("standupbot.api.digests")

router = APIRouter()


def _digest_to_response(digest) -> DigestResponse:
    """Convert a Digest ORM object to DigestResponse schema."""
    return DigestResponse(
        id=digest.id,
        team_id=digest.team_id,
        digest_date=digest.digest_date,
        ai_summary=digest.ai_summary,
        total_members=digest.total_members,
        responded_count=digest.responded_count,
        response_rate=format_response_rate(digest.responded_count, digest.total_members),
        non_responders=[nr.get("name", "") for nr in (digest.non_responders or [])],
        blockers=digest.blockers or [],
        entries=[],  # Entries are internal; expose via entries endpoint if needed
        status=digest.status,
        sent_at=digest.sent_at,
        created_at=digest.created_at,
    )


def _digest_to_list_item(digest) -> DigestListItem:
    """Convert a Digest ORM object to DigestListItem schema."""
    return DigestListItem(
        id=digest.id,
        digest_date=digest.digest_date,
        total_members=digest.total_members,
        responded_count=digest.responded_count,
        response_rate=format_response_rate(digest.responded_count, digest.total_members),
        status=digest.status,
        sent_at=digest.sent_at,
    )


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
    service = DigestService(db)
    digest = await service.get_todays_digest(team_id, user_id)
    if not digest:
        return None
    return _digest_to_response(digest)


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
    service = DigestService(db)
    digests = await service.get_digest_history(team_id, user_id, page, page_size)
    return [_digest_to_list_item(d) for d in digests]


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
    service = DigestService(db)
    digest = await service.get_digest_by_id(team_id, digest_id, user_id)
    return _digest_to_response(digest)


@router.post(
    "/{team_id}/trigger",
    response_model=MessageResponse,
    summary="Manually trigger digest",
    description="Manually trigger digest generation for a team (re-generates if exists).",
)
async def trigger_digest(
    team_id: UUID,
    user_id: CurrentUserId,
    db: DBSession,
) -> MessageResponse:
    """
    Manually trigger digest generation.

    USE CASES:
    - Manager wants to see the digest before the scheduled time
    - Re-generate after late submissions came in
    - Testing / debugging
    """
    service = DigestService(db)
    # Verify the user owns this team before triggering
    await service._verify_team_owner(team_id, user_id)
    digest = await service.generate_digest(team_id)

    logger.info(f"Manual digest triggered for team {team_id} by user {user_id}")

    return MessageResponse(
        message=(
            f"Digest generated: {digest.responded_count}/{digest.total_members} "
            f"responded, {len(digest.blockers or [])} blockers detected."
        )
    )
