"""
StandupBot — Digest Service

Assembles daily digests from submissions, detects blockers, calls LLM
for AI summary, and persists the result.

DATA FLOW — DAILY DIGEST GENERATION:
=====================================

  digest_time triggers (e.g., 10:00AM in team's timezone)
      │
      ▼
  DigestService.generate_digest(team_id, date)
      │
      ├─ 1. Fetch team + active members
      ├─ 2. Fetch all submissions for the date (via SubmissionService)
      ├─ 3. Identify non-responders (members - submitted members)
      ├─ 4. For each submission:
      │      └─ Check each answer for blockers (keyword + LLM)
      ├─ 5. Format submissions for LLM prompt
      ├─ 6. Call LLM for AI summary (with fallback to None)
      ├─ 7. Build Digest + DigestEntry records
      ├─ 8. Save to DB
      └─ 9. Return the complete digest
                │
                ▼
          (Module 5 dispatches via email/Slack)
"""

import logging
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import AuthorizationError, NotFoundError
from app.models.digest import Digest, DigestEntry
from app.models.member import Member
from app.models.question import Question
from app.models.submission import Submission
from app.models.team import Team
from app.services.llm_service import BaseLLMService, get_llm_service
from app.utils.helpers import detect_blocker_keywords, format_response_rate, today_utc

logger = logging.getLogger("standupbot.services.digest")


class DigestService:
    """
    Service for digest generation and retrieval.

    The digest is the core deliverable — it's what the manager receives
    every day summarizing their team's standup responses.
    """

    def __init__(self, db: AsyncSession, llm_service: BaseLLMService | None = None) -> None:
        self.db = db
        # Allow injecting a mock LLM service for testing
        self._llm = llm_service or get_llm_service()

    # ──────────────────────────────────────────────────────────────────
    # 1. GENERATE DIGEST — The main pipeline
    # ──────────────────────────────────────────────────────────────────

    async def generate_digest(
        self, team_id: UUID, digest_date: date | None = None
    ) -> Digest:
        """
        Generate a digest for a team.

        This is the CORE function of the product. Everything else exists
        to feed data into this function or display its output.

        Steps:
        1. Fetch team + active members
        2. Collect all submissions for the day
        3. Identify non-responders
        4. Flag entries with blockers (keyword + LLM)
        5. Call LLM for AI summary (with fallback)
        6. Assemble Digest + DigestEntry records
        7. Save to DB
        8. Return the digest

        IDEMPOTENCY: If a digest already exists for this team+date,
        we delete it and regenerate. This allows manual re-triggers.
        """
        target_date = digest_date or today_utc()

        # ── Step 1: Fetch team + active members ──
        stmt = (
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == team_id, Team.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundError(resource="Team")

        active_members = [m for m in team.members if m.is_active]
        total_members = len(active_members)

        # ── Step 2: Fetch all submissions for the date ──
        sub_stmt = (
            select(Submission)
            .options(
                selectinload(Submission.answers),
                selectinload(Submission.member),
            )
            .where(
                Submission.team_id == team_id,
                Submission.standup_date == target_date,
            )
        )
        result = await self.db.execute(sub_stmt)
        submissions = list(result.scalars().all())

        responded_member_ids = {s.member_id for s in submissions}
        responded_count = len(responded_member_ids)

        # ── Step 3: Identify non-responders ──
        non_responders = [
            {"id": str(m.id), "name": m.name, "email": m.email}
            for m in active_members
            if m.id not in responded_member_ids
        ]

        # ── Step 4: Detect blockers + build question lookup ──
        # Load questions for text lookup
        q_stmt = select(Question).where(Question.team_id == team_id)
        result = await self.db.execute(q_stmt)
        questions_map = {q.id: q.text for q in result.scalars().all()}

        all_blockers: list[dict] = []
        submission_blockers: dict[UUID, bool] = {}  # member_id -> has_blocker

        for submission in submissions:
            member_has_blocker = False
            answer_texts = [a.answer_text for a in submission.answers]

            # Keyword detection (fast, always works)
            for answer in submission.answers:
                if detect_blocker_keywords(answer.answer_text):
                    member_has_blocker = True
                    all_blockers.append({
                        "member_id": str(submission.member_id),
                        "member_name": submission.member.name,
                        "answer_text": answer.answer_text,
                        "question_text": questions_map.get(answer.question_id, ""),
                        "detection": "keyword",
                    })

            # LLM detection (try, but never block on failure)
            try:
                llm_blockers = await self._llm.detect_blockers(answer_texts)
                for blocker_text in llm_blockers:
                    # Avoid duplicates (keyword may have already caught it)
                    already_caught = any(
                        b["answer_text"] == blocker_text
                        for b in all_blockers
                        if b["member_id"] == str(submission.member_id)
                    )
                    if not already_caught:
                        member_has_blocker = True
                        all_blockers.append({
                            "member_id": str(submission.member_id),
                            "member_name": submission.member.name,
                            "answer_text": blocker_text,
                            "question_text": "",
                            "detection": "llm",
                        })
            except Exception as e:
                logger.error(f"LLM blocker detection failed: {e}")
                # Keyword results are still valid — continue

            submission_blockers[submission.member_id] = member_has_blocker

        # ── Step 5: Format submissions for LLM summary ──
        formatted_submissions = []
        for submission in submissions:
            answers_for_llm = []
            for answer in submission.answers:
                answers_for_llm.append({
                    "question_text": questions_map.get(answer.question_id, ""),
                    "answer_text": answer.answer_text,
                })
            formatted_submissions.append({
                "member_name": submission.member.name,
                "answers": answers_for_llm,
            })

        # ── Step 6: Call LLM for AI summary (with fallback) ──
        ai_summary = None
        if formatted_submissions:  # Only call LLM if there are submissions
            try:
                ai_summary = await self._llm.generate_summary(team.name, formatted_submissions)
            except Exception as e:
                logger.error(f"LLM summary generation failed for team {team.name}: {e}")
            # ai_summary stays None — digest sends without summary

        # ── Step 7: Build raw content (always available, even without AI) ──
        raw_lines = []
        for submission in submissions:
            raw_lines.append(f"## {submission.member.name}")
            for answer in submission.answers:
                q_text = questions_map.get(answer.question_id, "Question")
                raw_lines.append(f"**{q_text}:** {answer.answer_text}")
            raw_lines.append("")
        raw_content = "\n".join(raw_lines) if raw_lines else None

        # ── Step 8: Delete existing digest for idempotency ──
        existing_stmt = select(Digest).where(
            Digest.team_id == team_id,
            Digest.digest_date == target_date,
        )
        result = await self.db.execute(existing_stmt)
        existing = result.scalar_one_or_none()
        if existing:
            # Delete old entries first
            for entry in existing.entries:
                await self.db.delete(entry)
            await self.db.delete(existing)
            await self.db.flush()
            logger.info(f"Deleted existing digest for team={team_id} date={target_date}")

        # ── Step 9: Create Digest record ──
        digest = Digest(
            team_id=team_id,
            digest_date=target_date,
            ai_summary=ai_summary,
            raw_content=raw_content,
            total_members=total_members,
            responded_count=responded_count,
            non_responders=[{"name": nr["name"], "email": nr["email"]} for nr in non_responders],
            blockers=all_blockers,
            status="pending",  # Will become "sent" after email/Slack dispatch
        )
        self.db.add(digest)
        await self.db.flush()

        # Create DigestEntry records (one per active member)
        for member in active_members:
            submission_for_member = next(
                (s for s in submissions if s.member_id == member.id), None
            )
            entry = DigestEntry(
                digest_id=digest.id,
                member_id=member.id,
                submission_id=submission_for_member.id if submission_for_member else None,
                has_blocker=submission_blockers.get(member.id, False),
            )
            self.db.add(entry)

        await self.db.flush()

        logger.info(
            f"Digest generated: team={team.name} date={target_date} "
            f"responded={responded_count}/{total_members} "
            f"blockers={len(all_blockers)} ai_summary={'yes' if ai_summary else 'no'}"
        )
        return digest

    # ──────────────────────────────────────────────────────────────────
    # 2. RETRIEVAL METHODS — For the dashboard/API
    # ──────────────────────────────────────────────────────────────────

    async def get_todays_digest(self, team_id: UUID, owner_id: UUID) -> Digest | None:
        """Get today's digest for a team. Returns None if not yet generated."""
        await self._verify_team_owner(team_id, owner_id)

        stmt = (
            select(Digest)
            .options(selectinload(Digest.entries))
            .where(
                Digest.team_id == team_id,
                Digest.digest_date == today_utc(),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_digest_history(
        self, team_id: UUID, owner_id: UUID, page: int = 1, page_size: int = 20
    ) -> list[Digest]:
        """Get paginated digest history, most recent first."""
        await self._verify_team_owner(team_id, owner_id)

        offset = (page - 1) * page_size
        stmt = (
            select(Digest)
            .where(Digest.team_id == team_id)
            .order_by(Digest.digest_date.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_digest_by_id(
        self, team_id: UUID, digest_id: UUID, owner_id: UUID
    ) -> Digest:
        """Get a specific digest by ID."""
        await self._verify_team_owner(team_id, owner_id)

        stmt = (
            select(Digest)
            .options(selectinload(Digest.entries))
            .where(Digest.id == digest_id, Digest.team_id == team_id)
        )
        result = await self.db.execute(stmt)
        digest = result.scalar_one_or_none()
        if not digest:
            raise NotFoundError(resource="Digest")
        return digest

    # ──────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────

    async def _verify_team_owner(self, team_id: UUID, owner_id: UUID) -> Team:
        """Verify the user owns this team."""
        stmt = select(Team).where(Team.id == team_id, Team.deleted_at.is_(None))
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundError(resource="Team")
        if str(team.owner_id) != str(owner_id):
            raise AuthorizationError("You do not own this team")
        return team
