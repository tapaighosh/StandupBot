"""
StandupBot — Token Service (Link Engine)

Handles generation, validation, and lifecycle of standup magic link tokens.

SECURITY MODEL — Why JWTs AND a DB hash?
=========================================

We use TWO complementary security mechanisms:

1. JWT (JSON Web Token) — THE MAGIC LINK
   - The token in the URL is a digitally signed JWT
   - Contains: member_id, team_id, standup_date, expiry
   - Signed with our JWT_SECRET_KEY (same key used for auth tokens)
   - ANYONE who has this string can submit a standup — that's the "magic" part
   - The signature means it CAN'T be forged or tampered with

   WHY JWT for magic links?
   - Self-contained: we can read member_id/team_id without a DB lookup
   - Tamper-proof: changing any field invalidates the signature
   - The URL looks clean: /standup/<jwt_string>

2. DATABASE HASH — THE REVOCATION LAYER
   - We store a SHA-256 hash of each token in `standup_tokens` table
   - This lets us:
     a) Detect reuse (is_used flag)
     b) Revoke tokens (delete the row → validation fails)
     c) Audit who submitted and when
     d) Enforce one-token-per-member-per-day (idempotency)

   WHY NOT just rely on the JWT?
   - JWTs are stateless — once issued, they're valid until expiry
   - We can't "cancel" a JWT without a server-side check
   - We need to track is_used to prevent double submissions
   - We need an audit trail of all issued tokens

   WHY HASH instead of storing the raw token?
   - If the DB is compromised, the attacker gets hashes, not valid tokens
   - They can't reconstruct the original JWT from the hash
   - Same principle as password hashing

TOKEN LIFECYCLE:
  1. ReminderJob calls generate_daily_tokens(team_id)
  2. For each member, a JWT is created and hashed into the DB
  3. The magic link (FRONTEND_URL/standup/<jwt>) is sent via email/Slack
  4. Member clicks the link → frontend calls GET /submissions/form/<jwt>
  5. Backend calls validate_token(jwt) → checks signature + DB hash + status
  6. Member fills the form → frontend calls POST /submissions/form/<jwt>
  7. Backend calls mark_token_used(jwt) → sets is_used=True
"""

import hashlib
import logging
from datetime import date, datetime, time, timezone
from uuid import UUID

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.exceptions import AuthenticationError, NotFoundError, TokenExpiredError, TokenUsedError
from app.models.member import Member
from app.models.team import Team
from app.models.token import StandupToken

logger = logging.getLogger("standupbot.services.token")


def _hash_token(token: str) -> str:
    """
    Create a SHA-256 hash of a token string.

    WHY SHA-256?
    - Fast enough for per-request validation
    - One-way: can't reverse the hash to get the token
    - Deterministic: same input always produces the same hash
      (so we can look it up in the DB)
    """
    return hashlib.sha256(token.encode()).hexdigest()


def _compute_expiry(team: Team, standup_date: date) -> datetime:
    """
    Calculate the token expiry time based on team's submission_window_end.

    EXAMPLE:
      Team timezone = "America/New_York"
      submission_window_end = 11:00
      standup_date = 2026-04-16

      → Token expires at 2026-04-16 11:00:00 America/New_York
      → Converted to UTC for storage

    WHY USE THE TEAM'S TIMEZONE?
    The submission window (e.g., 6AM–11AM) is in the TEAM's timezone.
    A team in New York has a different 11AM than a team in London.
    We convert to UTC for consistent storage and comparison.
    """
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(team.timezone)
    except (KeyError, Exception):
        # Fallback to UTC if timezone is invalid
        tz = timezone.utc

    window_end = team.submission_window_end
    local_expiry = datetime.combine(standup_date, window_end, tzinfo=tz)

    # If late submissions are allowed, extend by 24 hours
    if team.allow_late_submissions:
        from datetime import timedelta
        local_expiry = local_expiry + timedelta(hours=24)

    return local_expiry


class TokenService:
    """
    Service for standup magic link token management.

    Each method is documented with WHAT it does and WHY.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────────────────────────────────
    # 1. GENERATE TOKEN
    # ──────────────────────────────────────────────────────────────────

    async def generate_token(
        self, member_id: UUID, team_id: UUID, standup_date: date
    ) -> str:
        """
        Generate a unique, time-scoped magic link token for a member.

        IDEMPOTENCY:
        If a token already exists for this member+team+date,
        we DON'T create a new one. We return a fresh JWT that will
        hash to the same DB record. This prevents:
        - Duplicate rows if the reminder job runs twice
        - Multiple valid tokens floating around for the same standup

        STEPS:
        1. Load the team (for timezone + submission window config)
        2. Check if a token already exists for this member+date
        3. If yes, return the existing token (re-generate the JWT)
        4. If no, create JWT → hash → store in DB → return JWT
        """
        # Load team for timezone and window config
        stmt = select(Team).where(Team.id == team_id)
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()
        if not team:
            raise NotFoundError(resource="Team")

        # Calculate expiry from team's submission window
        expires_at = _compute_expiry(team, standup_date)

        # Check for existing token (idempotency)
        existing_stmt = select(StandupToken).where(
            StandupToken.member_id == member_id,
            StandupToken.team_id == team_id,
            StandupToken.standup_date == standup_date,
        )
        result = await self.db.execute(existing_stmt)
        existing_token = result.scalar_one_or_none()

        if existing_token:
            # Re-generate the same JWT (it will hash to the same value)
            # This is safe because the claims are identical
            token_str = self._create_jwt(member_id, team_id, standup_date, expires_at)
            logger.info(
                f"Token already exists for member={member_id} date={standup_date}, returning existing"
            )
            return token_str

        # Create the JWT
        token_str = self._create_jwt(member_id, team_id, standup_date, expires_at)
        token_hash = _hash_token(token_str)

        # Store the hash in DB
        db_token = StandupToken(
            member_id=member_id,
            team_id=team_id,
            standup_date=standup_date,
            token_hash=token_hash,
            expires_at=expires_at,
            is_used=False,
        )
        self.db.add(db_token)
        await self.db.flush()

        logger.info(f"Token generated for member={member_id} date={standup_date}")
        return token_str

    def _create_jwt(
        self,
        member_id: UUID,
        team_id: UUID,
        standup_date: date,
        expires_at: datetime,
    ) -> str:
        """
        Create the actual JWT string.

        CLAIMS:
        - sub: member_id (who this token is for)
        - team_id: which team
        - date: standup date (YYYY-MM-DD)
        - exp: when this token expires
        - type: "standup" (distinguishes from auth JWTs)

        WHY "type": "standup"?
        We reuse the same JWT_SECRET_KEY for auth and standup tokens.
        The "type" claim prevents someone from using an auth access_token
        as a standup token (or vice versa). This is the same pattern
        we use to separate access vs refresh tokens.
        """
        payload = {
            "sub": str(member_id),
            "team_id": str(team_id),
            "date": standup_date.isoformat(),
            "exp": expires_at,
            "type": "standup",
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # ──────────────────────────────────────────────────────────────────
    # 2. VALIDATE TOKEN
    # ──────────────────────────────────────────────────────────────────

    async def validate_token(self, token_str: str) -> dict:
        """
        Validate a standup magic link token.

        VALIDATION CHAIN (order matters):
        1. Decode JWT → checks signature + expiry (crypto layer)
        2. Check type claim == "standup" (prevents auth token reuse)
        3. Look up hash in DB (revocation layer)
        4. Check is_used flag (prevents double submission)
        5. Check member is active (prevents removed members from submitting)
        6. Check team is active + not deleted (prevents submissions to dead teams)

        If ANY check fails, we raise a specific exception so the frontend
        can show the right error message to the user:
        - TokenExpiredError → "This link has expired"
        - TokenUsedError → "You've already submitted today"
        - AuthenticationError → "Invalid link" (catch-all)

        Returns: { member_id: UUID, team_id: UUID, standup_date: date }
        """
        # Step 1: Decode JWT (checks signature + expiry)
        try:
            payload = jwt.decode(
                token_str,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
        except JWTError as e:
            error_msg = str(e).lower()
            if "expired" in error_msg:
                raise TokenExpiredError("This standup link has expired")
            raise AuthenticationError(f"Invalid standup token: {e}")

        # Step 2: Check token type
        if payload.get("type") != "standup":
            raise AuthenticationError("Invalid token type — this is not a standup link")

        # Step 3: Look up hash in DB
        token_hash = _hash_token(token_str)
        stmt = select(StandupToken).where(StandupToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise AuthenticationError("Token not found — it may have been revoked")

        # Step 4: Check if already used
        if db_token.is_used:
            raise TokenUsedError("You have already submitted your standup for today")

        # Step 5: Check expiry from DB record (belt-and-suspenders with JWT exp)
        now = datetime.now(timezone.utc)
        if db_token.expires_at.tzinfo is None:
            # Ensure we can compare
            db_expiry = db_token.expires_at.replace(tzinfo=timezone.utc)
        else:
            db_expiry = db_token.expires_at
        if now > db_expiry:
            raise TokenExpiredError("This standup link has expired")

        # Step 6: Check member is active
        member_stmt = (
            select(Member)
            .options(selectinload(Member.team))
            .where(Member.id == db_token.member_id)
        )
        result = await self.db.execute(member_stmt)
        member = result.scalar_one_or_none()

        if not member or not member.is_active:
            raise AuthenticationError("This member is no longer active")

        # Step 7: Check team is active and not deleted
        team = member.team
        if not team or not team.is_active or team.deleted_at is not None:
            raise AuthenticationError("This team is no longer active")

        return {
            "member_id": db_token.member_id,
            "team_id": db_token.team_id,
            "standup_date": db_token.standup_date,
        }

    # ──────────────────────────────────────────────────────────────────
    # 3. MARK TOKEN USED
    # ──────────────────────────────────────────────────────────────────

    async def mark_token_used(self, token_str: str) -> None:
        """
        Mark a token as used after the member submits their standup.

        Once marked, the token hash's is_used flag = True,
        so validate_token() will reject it on future attempts.
        This prevents double-submission.
        """
        token_hash = _hash_token(token_str)
        stmt = select(StandupToken).where(StandupToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        db_token = result.scalar_one_or_none()

        if not db_token:
            raise AuthenticationError("Token not found")

        db_token.is_used = True
        db_token.used_at = datetime.now(timezone.utc)
        await self.db.flush()

        logger.info(f"Token marked as used: member={db_token.member_id} date={db_token.standup_date}")

    # ──────────────────────────────────────────────────────────────────
    # 4. GENERATE DAILY TOKENS
    # ──────────────────────────────────────────────────────────────────

    async def generate_daily_tokens(self, team_id: UUID) -> list[dict]:
        """
        Generate tokens for ALL active members of a team for today.

        This is called by the ReminderJob (Module 5) at the team's
        configured reminder_time. It returns everything the notification
        service needs to send magic links.

        RETURNS a list of dicts:
        [
          {
            "member_id": UUID,
            "email": "alice@example.com",
            "name": "Alice",
            "token": "eyJ...",
            "magic_link": "http://localhost:5173/standup/eyJ..."
          },
          ...
        ]
        """
        # Load team with members
        stmt = (
            select(Team)
            .options(selectinload(Team.members))
            .where(Team.id == team_id, Team.deleted_at.is_(None))
        )
        result = await self.db.execute(stmt)
        team = result.scalar_one_or_none()

        if not team:
            raise NotFoundError(resource="Team")

        today = date.today()
        tokens = []

        for member in team.members:
            if not member.is_active:
                continue

            token_str = await self.generate_token(
                member_id=member.id,
                team_id=team_id,
                standup_date=today,
            )

            magic_link = f"{settings.FRONTEND_URL}/standup/{token_str}"

            tokens.append({
                "member_id": member.id,
                "email": member.email,
                "name": member.name,
                "token": token_str,
                "magic_link": magic_link,
            })

        logger.info(f"Generated {len(tokens)} daily tokens for team={team_id}")
        return tokens
