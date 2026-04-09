"""
StandupBot — Submissions API Routes

Public endpoints for standup form rendering and submission.
These use token-based auth (no user login required).
Implementation stubs — full logic in Modules 2 & 3.
"""

from fastapi import APIRouter

from app.dependencies import DBSession
from app.schemas.submission import (
    StandupFormResponse,
    SubmissionConfirmation,
    SubmissionCreateRequest,
)

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

    - Checks token validity, expiry, and usage status
    - Returns the team's custom questions
    - Returns member name and standup date
    """
    # TODO: Implement in Module 2 (Token validation) + Module 3 (Form loading)
    raise NotImplementedError("Module 2/3: Submissions — Load form")


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

    - Validates the token (expiry, usage)
    - Checks submission window
    - Stores the submission and answers
    - Marks the token as used
    """
    # TODO: Implement in Module 2 (Token validation) + Module 3 (Submission)
    raise NotImplementedError("Module 2/3: Submissions — Submit standup")
