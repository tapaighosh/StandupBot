"""
StandupBot — Team Service

Business logic for team CRUD, member management, and question configuration.

AUTHORIZATION PATTERN:
  Every method that modifies a team takes `owner_id` as a parameter.
  Before doing anything, we verify the team's `owner_id` matches the caller.
  If it doesn't → 403 AuthorizationError.

  This is called "resource-level authorization":
  - Authentication (JWT) tells us WHO the user is
  - Authorization (this code) tells us WHAT they can do

  WHY NOT USE MIDDLEWARE?
  Because the check depends on the specific team being accessed.
  We can't know which team until we load it from the DB.

PLAN LIMITS:
  Each user has a Subscription (defaulting to "free" plan).
  Free tier: 1 team, 5 members per team.
  Before creating a team or inviting a member, we count existing resources
  and compare against the plan's limit.

  Plan limits are defined as constants (PLAN_LIMITS dict below).
  When billing (Module 7) is implemented, upgrading the subscription
  automatically raises the limits — no code changes needed.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import AuthorizationError, ConflictError, NotFoundError, PlanLimitError
from app.models.member import Member
from app.models.question import Question
from app.models.subscription import Subscription
from app.models.team import Team, TeamSettings
from app.schemas.team import TeamCreateRequest, TeamUpdateRequest

logger = logging.getLogger("standupbot.services.team")


# ──────────────────────────────────────────────────────────────────────
# PLAN LIMITS — How billing restrictions work
# ──────────────────────────────────────────────────────────────────────

# Each plan defines the max number of teams and members allowed.
# When a user tries to create a team or invite a member, we check
# their current subscription plan against these limits.
PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {"max_teams": 1, "max_members_per_team": 5},
    "starter": {"max_teams": 1, "max_members_per_team": 15},
    "growth": {"max_teams": 5, "max_members_per_team": 50},
}

# Default 3 standup questions that every new team starts with
DEFAULT_QUESTIONS = [
    "What did you accomplish yesterday?",
    "What are you working on today?",
    "Any blockers or help needed?",
]


class TeamService:
    """
    Service for team and member management.

    All methods take `owner_id` to enforce ownership-based authorization.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # PRIVATE HELPERS
    # ──────────────────────────────────────────────────────────────────

    async def _get_user_plan(self, owner_id: UUID) -> str:
        """
        Look up which billing plan the user is on.

        If no Subscription row exists, they're on the free plan.
        This will be populated when Module 7 (Billing) is implemented.
        """
        stmt = select(Subscription.plan).where(Subscription.user_id == owner_id)
        result = await self.db.execute(stmt)
        plan = result.scalar_one_or_none()
        return plan or "free"

    async def _get_team_with_owner_check(self, team_id: UUID, owner_id: UUID) -> Team:
        """
        Load a team by ID and verify the caller owns it.

        This is the core authorization check used by every mutating method.
        If the team doesn't exist → 404.
        If the caller isn't the owner → 403.
        If the team is soft-deleted → 404.

        WHY CHECK DELETED_AT?
        Soft-deleted teams still exist in the DB (for audit purposes),
        but they shouldn't be accessible through the API.
        """
        stmt = (
            select(Team)
            .options(
                selectinload(Team.members),
                selectinload(Team.questions),
                selectinload(Team.settings),
            )
            .where(Team.id == team_id)
        )
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()

        if not team or team.deleted_at is not None:
            raise NotFoundError(resource="Team")

        # Convert to UUID for comparison — owner_id might be a string from JWT
        from uuid import UUID as _UUID
        owner_uuid = owner_id if isinstance(owner_id, _UUID) else _UUID(str(owner_id))
        if team.owner_id != owner_uuid:
            raise AuthorizationError("You do not own this team")

        return team

    # ──────────────────────────────────────────────────────────────────
    # 1. CREATE TEAM
    # ──────────────────────────────────────────────────────────────────

    async def create_team(self, owner_id: UUID, data: TeamCreateRequest) -> Team:
        """
        Create a new team with default questions and settings in one transaction.

        WHAT HAPPENS IN ONE create_team() CALL:
        1. Check plan limit (free: 1 team max)
        2. Create the Team row
        3. Create 3 default Question rows (or custom if provided)
        4. Create 1 TeamSettings row with defaults
        5. Flush to DB (all in one transaction)

        WHY ONE TRANSACTION?
        If step 4 fails, we don't want an orphaned team without settings.
        `flush()` sends SQL without committing. The actual commit happens
        in the database session handler (database.py).
        """
        # Step 1: Enforce plan team limit
        plan = await self._get_user_plan(owner_id)
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

        # Count existing active (non-deleted) teams for this user
        stmt = (
            select(func.count())
            .select_from(Team)
            .where(Team.owner_id == owner_id, Team.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        team_count = result.scalar_one()

        if team_count >= limits["max_teams"]:
            raise PlanLimitError(
                f"Your {plan} plan allows a maximum of {limits['max_teams']} team(s). "
                "Please upgrade to create more teams."
            )

        # Step 2: Create the team
        team = Team(
            owner_id=owner_id,
            name=data.name,
            timezone=data.timezone,
            reminder_time=data.reminder_time,
            digest_time=data.digest_time,
            submission_window_start=data.submission_window_start,
            submission_window_end=data.submission_window_end,
            allow_late_submissions=data.allow_late_submissions,
            is_active=True,
        )
        self.db.add(team)
        await self.db.flush()  # Get team.id before creating children

        # Step 3: Create questions
        questions_data = data.questions
        if not questions_data:
            # Use defaults if none provided
            from app.schemas.team import QuestionCreate
            questions_data = [
                QuestionCreate(text=text, order_index=i)
                for i, text in enumerate(DEFAULT_QUESTIONS)
            ]

        for q_data in questions_data:
            question = Question(
                team_id=team.id,
                text=q_data.text,
                order_index=q_data.order_index,
                is_active=True,
            )
            self.db.add(question)

        # Step 4: Create default team settings
        settings = TeamSettings(
            team_id=team.id,
            email_reminders_enabled=True,
            slack_reminders_enabled=False,
            nudge_enabled=True,
            nudge_delay_minutes=120,
            low_response_alert_threshold=0.5,
        )
        self.db.add(settings)

        await self.db.flush()
        # Refresh to load relationships (questions, settings, members)
        await self.db.refresh(team, attribute_names=["questions", "settings", "members"])

        logger.info(f"Team created: {team.name} (id={team.id}) by user {owner_id}")
        return team

    # ──────────────────────────────────────────────────────────────────
    # 2. LIST TEAMS
    # ──────────────────────────────────────────────────────────────────

    async def list_teams(self, owner_id: UUID) -> list[Team]:
        """
        Return all active teams owned by a user, with member counts.

        ONLY returns non-deleted teams (deleted_at IS NULL).
        Members are loaded eagerly so we can count them without N+1 queries.

        N+1 PROBLEM EXPLAINED:
        Without eager loading, accessing team.members for 10 teams
        would fire 10 separate SQL queries (1 for teams + 10 for members).
        `selectinload` loads all members in a single extra query.
        """
        stmt = (
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.owner_id == owner_id, Team.deleted_at.is_(None))
            .order_by(Team.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # 3. GET TEAM
    # ──────────────────────────────────────────────────────────────────

    async def get_team(self, team_id: UUID, owner_id: UUID) -> Team:
        """
        Get a team by ID, verifying the caller is the owner.

        Returns the full team with questions, members, and settings loaded.
        """
        return await self._get_team_with_owner_check(team_id, owner_id)

    # ──────────────────────────────────────────────────────────────────
    # 4. UPDATE TEAM
    # ──────────────────────────────────────────────────────────────────

    async def update_team(
        self, team_id: UUID, owner_id: UUID, data: TeamUpdateRequest
    ) -> Team:
        """
        Partial update of team settings. Only non-None fields are updated.

        WHY PARTIAL UPDATE?
        The frontend only sends the fields that changed. We don't want to
        overwrite timezone when the user only changed the team name.
        `model_dump(exclude_unset=True)` gives us only the fields the
        client explicitly set.
        """
        team = await self._get_team_with_owner_check(team_id, owner_id)

        # model_dump(exclude_unset=True) returns only the fields that were
        # explicitly provided in the request body
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(team, field, value)

        await self.db.flush()
        logger.info(f"Team updated: {team.name} (id={team.id})")
        return team

    # ──────────────────────────────────────────────────────────────────
    # 5. DELETE TEAM (Soft Delete)
    # ──────────────────────────────────────────────────────────────────

    async def delete_team(self, team_id: UUID, owner_id: UUID) -> None:
        """
        Soft-delete a team: set deleted_at timestamp, deactivate all members.

        WHY SOFT DELETE?
        - We keep the data for audit/billing purposes.
        - If a user accidentally deletes a team, we could restore it.
        - Hard-delete would cascade and destroy submission history.

        WHAT GETS DEACTIVATED:
        - Team.is_active → False
        - Team.deleted_at → now
        - All members → is_active = False
        """
        team = await self._get_team_with_owner_check(team_id, owner_id)

        team.is_active = False
        team.deleted_at = datetime.now(timezone.utc)

        # Deactivate all team members
        for member in team.members:
            member.is_active = False

        await self.db.flush()
        logger.info(f"Team soft-deleted: {team.name} (id={team.id})")

    # ──────────────────────────────────────────────────────────────────
    # 6. INVITE MEMBER
    # ──────────────────────────────────────────────────────────────────

    async def invite_member(
        self, team_id: UUID, owner_id: UUID, email: str, name: str
    ) -> Member:
        """
        Invite a new member to a team.

        CHECKS:
        1. Verify ownership of the team
        2. Check for duplicate email within the same team
        3. Enforce plan member limit (free: 5 members max)
        4. Create the Member row

        WHY CHECK DUPLICATE WITHIN TEAM (NOT GLOBALLY)?
        A person could be a member of multiple teams.
        The uniqueness constraint is (team_id, email), not just email.
        """
        team = await self._get_team_with_owner_check(team_id, owner_id)

        # Check for duplicate email within this team
        # Include inactive members — re-invite should reactivate, not duplicate
        stmt = select(Member).where(
            Member.team_id == team_id,
            Member.email == email,
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            if existing.is_active:
                raise ConflictError(f"A member with email {email} already exists in this team")
            # Re-activate previously removed member
            existing.is_active = True
            existing.name = name
            await self.db.flush()
            logger.info(f"Member re-activated: {email} in team {team.name}")
            return existing

        # Enforce plan member limit
        plan = await self._get_user_plan(owner_id)
        limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

        active_count = sum(1 for m in team.members if m.is_active)
        if active_count >= limits["max_members_per_team"]:
            raise PlanLimitError(
                f"Your {plan} plan allows a maximum of {limits['max_members_per_team']} "
                "members per team. Please upgrade to invite more members."
            )

        # Create the member
        member = Member(
            team_id=team_id,
            email=email,
            name=name,
            is_active=True,
        )
        self.db.add(member)
        await self.db.flush()

        logger.info(f"Member invited: {email} to team {team.name} (id={team.id})")
        return member

    # ──────────────────────────────────────────────────────────────────
    # 7. LIST MEMBERS
    # ──────────────────────────────────────────────────────────────────

    async def list_members(self, team_id: UUID, owner_id: UUID) -> list[Member]:
        """
        List all ACTIVE members of a team.

        Inactive (removed) members are hidden from the API.
        They still exist in the DB for submission history.
        """
        # Verify ownership first
        await self._get_team_with_owner_check(team_id, owner_id)

        stmt = (
            select(Member)
            .where(Member.team_id == team_id, Member.is_active.is_(True))
            .order_by(Member.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    # ──────────────────────────────────────────────────────────────────
    # 8. REMOVE MEMBER
    # ──────────────────────────────────────────────────────────────────

    async def remove_member(
        self, team_id: UUID, member_id: UUID, owner_id: UUID
    ) -> None:
        """
        Soft-remove a member by setting is_active = False.

        WHY NOT HARD DELETE?
        The member may have past submissions and digest entries.
        Deleting the member row would cascade and destroy that data.
        """
        # Verify team ownership
        await self._get_team_with_owner_check(team_id, owner_id)

        # Find the member
        stmt = select(Member).where(
            Member.id == member_id,
            Member.team_id == team_id,
        )
        result = await self.db.execute(stmt)
        member = result.scalar_one_or_none()

        if not member:
            raise NotFoundError(resource="Member")

        if not member.is_active:
            raise NotFoundError(resource="Member")  # Already removed

        member.is_active = False
        await self.db.flush()

        logger.info(f"Member removed: {member.email} from team_id={team_id}")

    # ──────────────────────────────────────────────────────────────────
    # 9. UPDATE QUESTIONS
    # ──────────────────────────────────────────────────────────────────

    async def update_questions(
        self, team_id: UUID, owner_id: UUID, questions: list
    ) -> list[Question]:
        """
        Replace all questions for a team (full replacement strategy).

        WHY FULL REPLACEMENT?
        It's simpler than diffing which questions were added/removed/reordered.
        The frontend sends the full list; we deactivate old ones and create new ones.
        Old questions are kept (is_active=False) because existing Answers
        reference them via foreign key.
        """
        team = await self._get_team_with_owner_check(team_id, owner_id)

        # Deactivate all existing questions
        for q in team.questions:
            q.is_active = False

        # Create new questions
        new_questions = []
        for i, q_data in enumerate(questions):
            question = Question(
                team_id=team_id,
                text=q_data.text,
                order_index=q_data.order_index if q_data.order_index is not None else i,
                is_active=True,
            )
            self.db.add(question)
            new_questions.append(question)

        await self.db.flush()

        logger.info(f"Questions updated for team {team.name}: {len(new_questions)} questions")
        return new_questions
