"""
StandupBot — Submissions API Routes

PUBLIC endpoints for standup form rendering and submission.
These use TOKEN-based auth (magic links), NOT user login.

IMPORTANT: These routes are PUBLIC. No JWT header needed.
The token in the URL IS the authentication.

ROUTE MAP:
  GET  /form/{token}  — Load form (validate token, return questions)
  POST /form/{token}  — Submit standup (validate token, store answers)
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.dependencies import DBSession
from app.schemas.submission import (
    StandupFormResponse,
    SubmissionConfirmation,
    SubmissionCreateRequest,
)
from app.services.submission_service import SubmissionService
from app.services.token_service import TokenService

logger = logging.getLogger("standupbot.api.submissions")

router = APIRouter()


@router.get(
    "/form/{token}",
    response_model=StandupFormResponse,
    summary="Load standup form",
    description="Validate the magic link token and return the team's questions.",
)
async def load_form(token: str, db: DBSession) -> StandupFormResponse:
    """
    Validate a standup magic link token and return the form.

    THE FLOW:
    1. TokenService.validate_token() — checks signature, expiry, usage, member/team status
    2. SubmissionService.load_form() — loads team questions, checks if already submitted
    3. Returns the form data to the frontend

    POSSIBLE ERRORS:
    - 401 AuthenticationError: invalid/tampered token
    - 410 TokenExpiredError: token has expired
    - 409 TokenUsedError: token was already used (but we also check via load_form)
    """
    # Step 1: Validate the magic link token
    token_service = TokenService(db)
    token_data = await token_service.validate_token(token)

    # Step 2: Load the form
    submission_service = SubmissionService(db)
    form_data = await submission_service.load_form(
        member_id=token_data["member_id"],
        team_id=token_data["team_id"],
        standup_date=token_data["standup_date"],
    )

    return StandupFormResponse(
        team_name=form_data["team_name"],
        member_name=form_data["member_name"],
        standup_date=form_data["standup_date"],
        questions=form_data["questions"],
        already_submitted=form_data["already_submitted"],
    )


@router.post(
    "/form/{token}",
    response_model=SubmissionConfirmation,
    status_code=201,
    summary="Submit standup",
    description="Submit standup answers using a valid magic link token.",
)
async def submit_standup(
    token: str,
    request: SubmissionCreateRequest,
    db: DBSession,
) -> SubmissionConfirmation:
    """
    Submit a standup via magic link token.

    THE FLOW:
    1. TokenService.validate_token() — re-validate (prevents race conditions)
    2. SubmissionService.submit_standup() — window check, duplicate check, create records
    3. TokenService.mark_token_used() — prevent reuse
    4. Return confirmation

    WHY VALIDATE AGAIN ON POST?
    The GET (load_form) might have been minutes ago.
    Between GET and POST:
    - The token could have expired
    - The member could have been removed
    - The team could have been deleted
    So we validate again for safety.
    """
    # Step 1: Validate the token
    token_service = TokenService(db)
    token_data = await token_service.validate_token(token)

    # Step 2: Submit the standup
    submission_service = SubmissionService(db)
    submission = await submission_service.submit_standup(
        member_id=token_data["member_id"],
        team_id=token_data["team_id"],
        standup_date=token_data["standup_date"],
        answers=[
            {"question_id": a.question_id, "answer_text": a.answer_text}
            for a in request.answers
        ],
    )

    # Step 3: Mark token as used
    await token_service.mark_token_used(token)

    return SubmissionConfirmation(
        message="Your standup has been submitted successfully!",
        standup_date=submission.standup_date,
        submitted_at=submission.submitted_at,
    )
