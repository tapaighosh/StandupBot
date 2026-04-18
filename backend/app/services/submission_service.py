"""
StandupBot — Submission Service

Business logic for standup form loading and submission processing.

SUBMISSION FLOW (what happens when a member clicks their magic link):
=====================================================================

1. Member clicks magic link → GET /submissions/form/{token}
   - TokenService validates the JWT (signature, expiry, usage)
   - SubmissionService.load_form() fetches team questions
   - Returns: team name, member name, questions, already_submitted flag
   - If already_submitted=true, the frontend shows "already done" message

2. Member fills the form → POST /submissions/form/{token}
   - TokenService validates the token AGAIN (prevents race conditions)
   - SubmissionService.submit_standup() processes the answers:
     a. Checks submission window (is it between 6AM–11AM in team's timezone?)
     b. If outside window: reject UNLESS allow_late_submissions=true
     c. Checks for existing submission (prevent duplicate)
     d. Creates Submission + Answer records
     e. Marks the token as used
   - Returns: confirmation with date + timestamp

WHY CHECK THE WINDOW TWICE?
The token's expiry already enforces a rough deadline, but the submission
window is more precise. The token might expire at 11AM but the window
could be 6AM–10AM. The window check catches this.
"""

import logging
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import ConflictError, NotFoundError, SubmissionWindowClosedError
from app.models.member import Member
from app.models.question import Question
from app.models.submission import Answer, Submission
from app.models.team import Team
from app.services.token_service import TokenService
from app.utils.helpers import is_within_window, now_utc

logger = logging.getLogger("standupbot.services.submission")


class SubmissionService:
    """
    Service for standup submissions.

    PUBLIC METHODS:
    - load_form():  Load form data for a validated member
    - submit_standup(): Process a standup submission
    - get_submissions_for_date(): Get all submissions for a team+date (for digests)
    - get_member_submission(): Get a specific member's submission
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # 1. LOAD FORM
    # ──────────────────────────────────────────────────────────────────

    async def load_form(
        self, member_id: UUID, team_id: UUID, standup_date: date
    ) -> dict:
        """
        Load the standup form for a member.

        RETURNS:
        {
          "team_name": "Engineering Team",
          "member_name": "Alice",
          "standup_date": "2026-04-18",
          "questions": [
            {"id": "uuid", "text": "What did you accomplish?", "order_index": 0},
            ...
          ],
          "already_submitted": false
        }

        WHY CHECK already_submitted?
        If the member already submitted (e.g., they refreshed the page),
        the frontend shows a "you already submitted" screen instead
        of the form. This is a better UX than silently failing on POST.
        """
        # Load team
        stmt = select(Team).where(Team.id == team_id)
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundError(resource="Team")

        # Load member
        member_stmt = select(Member).where(Member.id == member_id)
        result = await self.db.execute(member_stmt)
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError(resource="Member")

        # Load active questions, ordered by order_index
        questions_stmt = (
            select(Question)
            .where(Question.team_id == team_id, Question.is_active.is_(True))
            .order_by(Question.order_index)
        )
        result = await self.db.execute(questions_stmt)
        questions = result.scalars().all()

        # Check for existing submission
        already_submitted = await self._has_submission(member_id, team_id, standup_date)

        return {
            "team_name": team.name,
            "member_name": member.name,
            "standup_date": standup_date,
            "questions": [
                {
                    "id": str(q.id),
                    "text": q.text,
                    "order_index": q.order_index,
                }
                for q in questions
            ],
            "already_submitted": already_submitted,
        }

    # ──────────────────────────────────────────────────────────────────
    # 2. SUBMIT STANDUP
    # ──────────────────────────────────────────────────────────────────

    async def submit_standup(
        self,
        member_id: UUID,
        team_id: UUID,
        standup_date: date,
        answers: list[dict],
    ) -> Submission:
        """
        Process a standup submission.

        STEPS:
        1. Load team (for window config)
        2. Check submission window
        3. Check for existing submission (prevent duplicate)
        4. Create Submission record
        5. Create Answer records (one per question)
        6. Flush to DB (one transaction)

        PARAMETERS:
        - answers: list of {"question_id": UUID, "answer_text": str}

        RETURNS: The created Submission object

        RAISES:
        - SubmissionWindowClosedError: if outside window and late subs disabled
        - ConflictError: if already submitted for this date
        """
        # Step 1: Load team
        stmt = select(Team).where(Team.id == team_id)
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundError(resource="Team")

        # Step 2: Check submission window
        now = now_utc()
        in_window = is_within_window(
            current_time=now,
            window_start=team.submission_window_start,
            window_end=team.submission_window_end,
            tz_name=team.timezone,
        )

        is_late = False
        if not in_window:
            if team.allow_late_submissions:
                # Allow but FLAG as late
                is_late = True
                logger.info(
                    f"Late submission from member={member_id} for team={team.name}"
                )
            else:
                raise SubmissionWindowClosedError(
                    f"The submission window ({team.submission_window_start.strftime('%H:%M')}"
                    f"–{team.submission_window_end.strftime('%H:%M')} {team.timezone}) has closed."
                )

        # Step 3: Check for existing submission
        existing = await self._has_submission(member_id, team_id, standup_date)
        if existing:
            raise ConflictError(
                "You have already submitted your standup for today. "
                "Each member can only submit once per day."
            )

        # Step 4: Create Submission
        submission = Submission(
            member_id=member_id,
            team_id=team_id,
            standup_date=standup_date,
            is_late=is_late,
            submitted_at=now,
        )
        self.db.add(submission)
        await self.db.flush()  # Get submission.id

        # Step 5: Create Answer records
        for answer_data in answers:
            answer = Answer(
                submission_id=submission.id,
                question_id=answer_data["question_id"],
                answer_text=answer_data["answer_text"],
            )
            self.db.add(answer)

        await self.db.flush()

        logger.info(
            f"Standup submitted: member={member_id} team={team.name} "
            f"date={standup_date} is_late={is_late}"
        )
        return submission

    # ──────────────────────────────────────────────────────────────────
    # 3. GET SUBMISSIONS FOR A DATE (used by Digest Engine)
    # ──────────────────────────────────────────────────────────────────

    async def get_submissions_for_date(
        self, team_id: UUID, standup_date: date
    ) -> list[Submission]:
        """
        Get all submissions for a team on a specific date.

        Used by the Digest Engine (Module 4) to compile the daily summary.
        Eagerly loads answers and member info.
        """
        stmt = (
            select(Submission)
            .options(
                selectinload(Submission.answers),
                selectinload(Submission.member),
            )
            .where(
                Submission.team_id == team_id,
                Submission.standup_date == standup_date,
            )
            .order_by(Submission.submitted_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # 4. GET SPECIFIC MEMBER'S SUBMISSION
    # ──────────────────────────────────────────────────────────────────

    async def get_member_submission(
        self, member_id: UUID, team_id: UUID, standup_date: date
    ) -> Submission | None:
        """Get a specific member's submission for a date."""
        stmt = (
            select(Submission)
            .options(selectinload(Submission.answers))
            .where(
                Submission.member_id == member_id,
                Submission.team_id == team_id,
                Submission.standup_date == standup_date,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ──────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────

    async def _has_submission(
        self, member_id: UUID, team_id: UUID, standup_date: date
    ) -> bool:
        """Check if a member has already submitted for a given date."""
        stmt = select(Submission.id).where(
            Submission.member_id == member_id,
            Submission.team_id == team_id,
            Submission.standup_date == standup_date,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None
