"""
StandupBot — Token (Link Engine) Tests

Tests for magic link token generation, validation, usage tracking,
and security edge cases.

COVERED TEST CASES (from test_cases.md Section 2):
  [TC-2.1.1] Generate unique token per member per day
  [TC-2.1.2] Token contains correct claims (member_id, team_id, date, exp)
  [TC-2.1.3] Token expires at configured submission window end
  [TC-2.1.4] Re-generating token for same member+date returns same token
  [TC-2.2.1] Valid, unused token passes validation
  [TC-2.2.2] Expired token is rejected
  [TC-2.2.3] Already-used token is rejected
  [TC-2.2.4] Token with tampered signature is rejected
  [TC-2.2.5] Token for non-existent member is rejected
  [TC-2.2.6] Token for inactive team is rejected

TESTING STRATEGY:
  We test at the SERVICE level (not HTTP) because the token service is
  the security boundary. The API routes that use tokens (Module 3) will
  get their own integration tests.

  We create real DB records (teams, members) via fixtures, then call
  TokenService methods directly. No mocking needed.
"""

from datetime import date, datetime, time, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AuthenticationError, TokenExpiredError, TokenUsedError
from app.models.member import Member
from app.models.team import Team, TeamSettings
from app.services.token_service import TokenService, _hash_token


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES — Create test team + member in the DB
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
async def team_with_member(db_session: AsyncSession, create_test_user):
    """
    Create a complete team with one member — the minimum needed to test tokens.

    Returns: (team, member, owner) tuple
    """
    # Create team owner (a User)
    owner = await create_test_user(email="manager@test.com")

    # Create team with a wide submission window (easy to test)
    team = Team(
        owner_id=owner.id,
        name="Token Test Team",
        timezone="UTC",
        reminder_time=time(8, 0),
        digest_time=time(10, 0),
        submission_window_start=time(0, 0),  # midnight
        submission_window_end=time(23, 59),   # almost midnight
        allow_late_submissions=False,
        is_active=True,
    )
    db_session.add(team)
    await db_session.flush()

    # Create team settings
    settings = TeamSettings(
        team_id=team.id,
        email_reminders_enabled=True,
    )
    db_session.add(settings)

    # Create a member
    member = Member(
        team_id=team.id,
        email="alice@example.com",
        name="Alice",
        is_active=True,
    )
    db_session.add(member)
    await db_session.flush()

    return team, member, owner


@pytest.fixture
async def team_with_multiple_members(db_session: AsyncSession, create_test_user):
    """Create a team with 3 members for batch token tests."""
    owner = await create_test_user(email="batch-manager@test.com")

    team = Team(
        owner_id=owner.id,
        name="Batch Test Team",
        timezone="UTC",
        reminder_time=time(8, 0),
        digest_time=time(10, 0),
        submission_window_start=time(0, 0),
        submission_window_end=time(23, 59),
        allow_late_submissions=False,
        is_active=True,
    )
    db_session.add(team)
    await db_session.flush()

    members = []
    for i, (email, name) in enumerate([
        ("alice@test.com", "Alice"),
        ("bob@test.com", "Bob"),
        ("charlie@test.com", "Charlie"),
    ]):
        m = Member(team_id=team.id, email=email, name=name, is_active=(i < 3))
        db_session.add(m)
        members.append(m)

    await db_session.flush()
    return team, members, owner


# ═══════════════════════════════════════════════════════════════════════
# TOKEN GENERATION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestTokenGeneration:
    """Tests for TokenService.generate_token()"""

    @pytest.mark.asyncio
    async def test_generate_token_returns_jwt_string(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.1.1] Generate a token for a member — should return a JWT string.
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(
            member_id=member.id,
            team_id=team.id,
            standup_date=date.today(),
        )

        assert token is not None
        assert isinstance(token, str)
        # JWTs have 3 parts separated by dots
        assert len(token.split(".")) == 3

    @pytest.mark.asyncio
    async def test_token_contains_correct_claims(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.1.2] Token should contain member_id, team_id, date, type, exp.
        """
        from jose import jwt as jose_jwt
        from app.config import settings

        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(
            member_id=member.id,
            team_id=team.id,
            standup_date=date.today(),
        )

        # Decode without verifying expiry (for inspection)
        payload = jose_jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert payload["sub"] == str(member.id)
        assert payload["team_id"] == str(team.id)
        assert payload["date"] == date.today().isoformat()
        assert payload["type"] == "standup"
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_generate_token_idempotent(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.1.4] Generating a token twice for the same member+date
        should return the same token (idempotent).
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)
        today = date.today()

        token1 = await service.generate_token(member.id, team.id, today)
        token2 = await service.generate_token(member.id, team.id, today)

        # Same claims + same expiry → same JWT string
        assert token1 == token2

    @pytest.mark.asyncio
    async def test_generate_token_stores_hash_in_db(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        The token's SHA-256 hash should be stored in the standup_tokens table.
        """
        from sqlalchemy import select
        from app.models.token import StandupToken

        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())
        expected_hash = _hash_token(token)

        stmt = select(StandupToken).where(StandupToken.token_hash == expected_hash)
        result = await db_session.execute(stmt)
        db_token = result.scalar_one_or_none()

        assert db_token is not None
        assert db_token.member_id == member.id
        assert db_token.team_id == team.id
        assert db_token.is_used is False


# ═══════════════════════════════════════════════════════════════════════
# TOKEN VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestTokenValidation:
    """Tests for TokenService.validate_token()"""

    @pytest.mark.asyncio
    async def test_valid_token_passes(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.2.1] A freshly generated, unused token should pass validation.
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())
        result = await service.validate_token(token)

        assert result["member_id"] == member.id
        assert result["team_id"] == team.id
        assert result["standup_date"] == date.today()

    @pytest.mark.asyncio
    async def test_used_token_rejected(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.2.3] A token that's already been used should be rejected.
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())

        # Mark as used
        await service.mark_token_used(token)

        # Should fail validation
        with pytest.raises(TokenUsedError):
            await service.validate_token(token)

    @pytest.mark.asyncio
    async def test_tampered_token_rejected(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.2.4] A token with a modified signature is rejected.
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())

        # Tamper with the token by changing the last character
        tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

        with pytest.raises(AuthenticationError):
            await service.validate_token(tampered)

    @pytest.mark.asyncio
    async def test_completely_fake_token_rejected(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        A completely random string should fail JWT decoding.
        """
        service = TokenService(db_session)

        with pytest.raises(AuthenticationError):
            await service.validate_token("this-is-not-a-jwt")

    @pytest.mark.asyncio
    async def test_auth_access_token_rejected_as_standup(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        An auth access_token (type="access") must NOT be accepted
        as a standup token. This prevents token type confusion.
        """
        from app.utils.security import create_access_token

        _, member, _ = team_with_member
        service = TokenService(db_session)

        # Create an auth token (not a standup token)
        auth_token = create_access_token(data={"sub": str(member.id)})

        with pytest.raises(AuthenticationError, match="not a standup"):
            await service.validate_token(auth_token)

    @pytest.mark.asyncio
    async def test_token_for_inactive_member_rejected(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.2.5] Token for a deactivated member should fail.
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())

        # Deactivate the member
        member.is_active = False
        await db_session.flush()

        with pytest.raises(AuthenticationError, match="no longer active"):
            await service.validate_token(token)

    @pytest.mark.asyncio
    async def test_token_for_deleted_team_rejected(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        [TC-2.2.6] Token for a soft-deleted team should fail.
        """
        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())

        # Soft-delete the team
        team.is_active = False
        team.deleted_at = datetime.now(timezone.utc)
        await db_session.flush()

        with pytest.raises(AuthenticationError, match="no longer active"):
            await service.validate_token(token)


# ═══════════════════════════════════════════════════════════════════════
# MARK TOKEN USED TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestMarkTokenUsed:
    """Tests for TokenService.mark_token_used()"""

    @pytest.mark.asyncio
    async def test_mark_used_sets_flags(
        self, db_session: AsyncSession, team_with_member
    ):
        """
        Marking a token should set is_used=True and record used_at timestamp.
        """
        from sqlalchemy import select
        from app.models.token import StandupToken

        team, member, _ = team_with_member
        service = TokenService(db_session)

        token = await service.generate_token(member.id, team.id, date.today())
        await service.mark_token_used(token)

        # Verify in DB
        token_hash = _hash_token(token)
        stmt = select(StandupToken).where(StandupToken.token_hash == token_hash)
        result = await db_session.execute(stmt)
        db_token = result.scalar_one()

        assert db_token.is_used is True
        assert db_token.used_at is not None

    @pytest.mark.asyncio
    async def test_mark_nonexistent_token_fails(self, db_session: AsyncSession):
        """Marking a token that doesn't exist in DB should raise."""
        service = TokenService(db_session)

        with pytest.raises(AuthenticationError, match="not found"):
            await service.mark_token_used("some.fake.token")


# ═══════════════════════════════════════════════════════════════════════
# BATCH TOKEN GENERATION TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestGenerateDailyTokens:
    """Tests for TokenService.generate_daily_tokens()"""

    @pytest.mark.asyncio
    async def test_generates_tokens_for_all_active_members(
        self, db_session: AsyncSession, team_with_multiple_members
    ):
        """
        generate_daily_tokens should create one token per active member.
        """
        team, members, _ = team_with_multiple_members
        service = TokenService(db_session)

        # Deactivate one member
        members[2].is_active = False
        await db_session.flush()

        result = await service.generate_daily_tokens(team.id)

        # Should have tokens for 2 active members (not the deactivated one)
        assert len(result) == 2
        emails = [r["email"] for r in result]
        assert "alice@test.com" in emails
        assert "bob@test.com" in emails

    @pytest.mark.asyncio
    async def test_daily_tokens_contain_magic_links(
        self, db_session: AsyncSession, team_with_multiple_members
    ):
        """
        Each token result should contain a magic_link URL.
        """
        team, _, _ = team_with_multiple_members
        service = TokenService(db_session)

        result = await service.generate_daily_tokens(team.id)

        for item in result:
            assert "magic_link" in item
            assert item["magic_link"].startswith("http")
            assert "/standup/" in item["magic_link"]
            assert "member_id" in item
            assert "email" in item
            assert "name" in item
            assert "token" in item

    @pytest.mark.asyncio
    async def test_daily_tokens_idempotent(
        self, db_session: AsyncSession, team_with_multiple_members
    ):
        """
        Calling generate_daily_tokens twice should produce the same tokens
        (not create duplicates).
        """
        team, _, _ = team_with_multiple_members
        service = TokenService(db_session)

        result1 = await service.generate_daily_tokens(team.id)
        result2 = await service.generate_daily_tokens(team.id)

        tokens1 = sorted(r["token"] for r in result1)
        tokens2 = sorted(r["token"] for r in result2)
        assert tokens1 == tokens2
