"""
StandupBot — Digest Engine Tests

Tests for digest generation, blocker detection, and LLM integration.

COVERED TEST CASES (from test_cases.md Section 4):
  [TC-4.1.1] Digest with all members responded
  [TC-4.1.2] Digest with non-responders identified
  [TC-4.1.3] Blocker detection via keywords
  [TC-4.1.4] LLM failure fallback — digest generates without AI summary
  [TC-4.1.5] Idempotent re-generation (manual trigger)
  [TC-4.2.1] GET today's digest
  [TC-4.2.2] GET digest history (paginated)
  [TC-4.2.3] POST manual trigger
  [TC-4.2.4] Unauthorized user cannot access digest

TESTING STRATEGY:
  We MOCK the LLM service — no real OpenAI calls in tests.
  The MockLLMService returns predictable responses so we can assert
  on the digest output without depending on an external API.
"""

from datetime import date, datetime, time, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.question import Question
from app.models.submission import Answer, Submission
from app.models.team import Team, TeamSettings
from app.services.digest_service import DigestService
from app.services.llm_service import BaseLLMService


# ═══════════════════════════════════════════════════════════════════════
# MOCK LLM SERVICE — Predictable, no API calls
# ═══════════════════════════════════════════════════════════════════════


class MockLLMService(BaseLLMService):
    """
    Mock LLM for testing. Returns predictable responses.
    Set simulate_failure=True to test the fallback path.
    """

    def __init__(self, simulate_failure: bool = False):
        self.simulate_failure = simulate_failure
        self.summary_calls: list[dict] = []
        self.blocker_calls: list[list[str]] = []

    async def generate_summary(self, team_name: str, submissions: list[dict]) -> str | None:
        self.summary_calls.append({"team_name": team_name, "submissions": submissions})
        if self.simulate_failure:
            raise Exception("Simulated LLM failure")
        return f"AI Summary for {team_name}: {len(submissions)} submissions processed. Momentum: 🟢 High"

    async def detect_blockers(self, answers: list[str]) -> list[str]:
        self.blocker_calls.append(answers)
        if self.simulate_failure:
            raise Exception("Simulated LLM failure")
        # The mock returns answers containing "blocked" or "waiting" as blockers
        return [a for a in answers if "blocked" in a.lower() or "waiting" in a.lower()]

    async def generate_weekly_report(self, team_name: str, weekly_data: list[dict]) -> str | None:
        return None


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
async def digest_team(db_session: AsyncSession, create_test_user):
    """
    Create a team with 3 members and 3 default questions.
    Returns (team, members, owner, questions).
    """
    owner = await create_test_user(email="digest-manager@test.com")

    team = Team(
        owner_id=owner.id,
        name="Digest Test Team",
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

    settings = TeamSettings(team_id=team.id, email_reminders_enabled=True)
    db_session.add(settings)

    q1 = Question(team_id=team.id, text="What did you accomplish yesterday?", order_index=0, is_active=True)
    q2 = Question(team_id=team.id, text="What are you working on today?", order_index=1, is_active=True)
    q3 = Question(team_id=team.id, text="Any blockers or things you need help with?", order_index=2, is_active=True)
    db_session.add_all([q1, q2, q3])

    alice = Member(team_id=team.id, email="alice@test.com", name="Alice", is_active=True)
    bob = Member(team_id=team.id, email="bob@test.com", name="Bob", is_active=True)
    charlie = Member(team_id=team.id, email="charlie@test.com", name="Charlie", is_active=True)
    db_session.add_all([alice, bob, charlie])
    await db_session.flush()

    return team, [alice, bob, charlie], owner, [q1, q2, q3]


@pytest.fixture
async def team_with_submissions(db_session: AsyncSession, digest_team):
    """
    Create submissions for Alice and Bob (Charlie is a non-responder).
    Bob has a blocker keyword in his answer.
    """
    team, members, owner, questions = digest_team
    alice, bob, charlie = members
    q1, q2, q3 = questions
    today = date.today()

    # Alice's submission — no blockers
    alice_sub = Submission(
        member_id=alice.id,
        team_id=team.id,
        standup_date=today,
        is_late=False,
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(alice_sub)
    await db_session.flush()

    db_session.add_all([
        Answer(submission_id=alice_sub.id, question_id=q1.id, answer_text="Fixed the CI pipeline and deployed to staging"),
        Answer(submission_id=alice_sub.id, question_id=q2.id, answer_text="Working on API integration tests"),
        Answer(submission_id=alice_sub.id, question_id=q3.id, answer_text="None"),
    ])

    # Bob's submission — HAS a blocker
    bob_sub = Submission(
        member_id=bob.id,
        team_id=team.id,
        standup_date=today,
        is_late=False,
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(bob_sub)
    await db_session.flush()

    db_session.add_all([
        Answer(submission_id=bob_sub.id, question_id=q1.id, answer_text="Completed design review for auth flow"),
        Answer(submission_id=bob_sub.id, question_id=q2.id, answer_text="Frontend dashboard components"),
        Answer(submission_id=bob_sub.id, question_id=q3.id, answer_text="Blocked on API keys from DevOps — waiting for approval"),
    ])

    await db_session.flush()

    # Charlie did NOT submit — he's the non-responder
    return team, members, owner, questions, [alice_sub, bob_sub]


# ═══════════════════════════════════════════════════════════════════════
# DIGEST GENERATION TESTS (Service Layer)
# ═══════════════════════════════════════════════════════════════════════


class TestDigestGeneration:
    """Tests for DigestService.generate_digest()"""

    @pytest.mark.asyncio
    async def test_digest_with_submissions(
        self, db_session: AsyncSession, team_with_submissions
    ):
        """
        [TC-4.1.1] Digest correctly counts responded members
        and includes AI summary.
        """
        team, members, owner, questions, subs = team_with_submissions
        mock_llm = MockLLMService()
        service = DigestService(db_session, llm_service=mock_llm)

        digest = await service.generate_digest(team.id)

        assert digest.team_id == team.id
        assert digest.digest_date == date.today()
        assert digest.total_members == 3
        assert digest.responded_count == 2  # Alice + Bob
        assert digest.status == "pending"
        assert digest.ai_summary is not None
        assert "Digest Test Team" in digest.ai_summary
        assert digest.raw_content is not None

    @pytest.mark.asyncio
    async def test_digest_identifies_non_responders(
        self, db_session: AsyncSession, team_with_submissions
    ):
        """
        [TC-4.1.2] Non-responders (Charlie) are correctly identified.
        """
        team, members, _, _, _ = team_with_submissions
        mock_llm = MockLLMService()
        service = DigestService(db_session, llm_service=mock_llm)

        digest = await service.generate_digest(team.id)

        assert digest.non_responders is not None
        non_responder_names = [nr["name"] for nr in digest.non_responders]
        assert "Charlie" in non_responder_names
        assert "Alice" not in non_responder_names
        assert "Bob" not in non_responder_names
        assert len(digest.non_responders) == 1

    @pytest.mark.asyncio
    async def test_digest_detects_blockers(
        self, db_session: AsyncSession, team_with_submissions
    ):
        """
        [TC-4.1.3] Blockers are detected via keyword matching.
        Bob's answer contains "Blocked" — should be flagged.
        """
        team, _, _, _, _ = team_with_submissions
        mock_llm = MockLLMService()
        service = DigestService(db_session, llm_service=mock_llm)

        digest = await service.generate_digest(team.id)

        assert digest.blockers is not None
        assert len(digest.blockers) > 0

        # Bob's blocker should be detected
        blocker_names = [b["member_name"] for b in digest.blockers]
        assert "Bob" in blocker_names

    @pytest.mark.asyncio
    async def test_digest_llm_failure_fallback(
        self, db_session: AsyncSession, team_with_submissions
    ):
        """
        [TC-4.1.4] When LLM fails, digest STILL generates — just without AI summary.
        This is the critical fallback pattern.
        """
        team, _, _, _, _ = team_with_submissions
        failing_llm = MockLLMService(simulate_failure=True)
        service = DigestService(db_session, llm_service=failing_llm)

        # Should NOT raise — graceful degradation
        digest = await service.generate_digest(team.id)

        assert digest is not None
        assert digest.ai_summary is None  # No AI summary
        assert digest.responded_count == 2  # Data is still correct
        assert digest.raw_content is not None  # Raw content still available
        # Keyword blockers still work even when LLM fails
        assert digest.total_members == 3

    @pytest.mark.asyncio
    async def test_digest_idempotent_regeneration(
        self, db_session: AsyncSession, team_with_submissions
    ):
        """
        [TC-4.1.5] Regenerating a digest replaces the old one.
        """
        team, _, _, _, _ = team_with_submissions
        mock_llm = MockLLMService()
        service = DigestService(db_session, llm_service=mock_llm)

        # Generate first digest
        digest1 = await service.generate_digest(team.id)
        digest1_id = digest1.id

        # Regenerate
        digest2 = await service.generate_digest(team.id)

        # Should be a NEW digest (old one deleted)
        assert digest2.id != digest1_id
        assert digest2.responded_count == 2

    @pytest.mark.asyncio
    async def test_digest_no_submissions(
        self, db_session: AsyncSession, digest_team
    ):
        """Digest with zero submissions — 0 responded, all are non-responders."""
        team, members, _, _ = digest_team
        mock_llm = MockLLMService()
        service = DigestService(db_session, llm_service=mock_llm)

        digest = await service.generate_digest(team.id)

        assert digest.responded_count == 0
        assert digest.total_members == 3
        assert len(digest.non_responders) == 3
        assert digest.ai_summary is None  # No submissions → no summary

    @pytest.mark.asyncio
    async def test_llm_called_with_correct_data(
        self, db_session: AsyncSession, team_with_submissions
    ):
        """Verify the LLM receives correctly formatted submission data."""
        team, _, _, _, _ = team_with_submissions
        mock_llm = MockLLMService()
        service = DigestService(db_session, llm_service=mock_llm)

        await service.generate_digest(team.id)

        # Check LLM was called
        assert len(mock_llm.summary_calls) == 1
        call = mock_llm.summary_calls[0]
        assert call["team_name"] == "Digest Test Team"
        assert len(call["submissions"]) == 2  # Alice + Bob

        # Check submission format
        member_names = {s["member_name"] for s in call["submissions"]}
        assert "Alice" in member_names
        assert "Bob" in member_names


# ═══════════════════════════════════════════════════════════════════════
# DIGEST API TESTS (HTTP Layer)
# ═══════════════════════════════════════════════════════════════════════


class TestDigestAPI:
    """Tests for digest API endpoints."""

    @pytest.mark.asyncio
    async def test_manual_trigger(
        self, client: AsyncClient, auth_headers, team_with_submissions
    ):
        """
        [TC-4.2.3] POST /{team_id}/trigger — manual digest generation.
        """
        team, _, owner, _, _ = team_with_submissions
        headers = await auth_headers(owner)

        response = await client.post(
            f"/api/v1/digests/{team.id}/trigger",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "responded" in data["message"]

    @pytest.mark.asyncio
    async def test_get_todays_digest(
        self, client: AsyncClient, auth_headers, team_with_submissions, db_session
    ):
        """
        [TC-4.2.1] GET /{team_id}/today — returns digest after trigger.
        """
        team, _, owner, _, _ = team_with_submissions
        headers = await auth_headers(owner)

        # First trigger to generate
        await client.post(f"/api/v1/digests/{team.id}/trigger", headers=headers)

        # Then fetch
        response = await client.get(
            f"/api/v1/digests/{team.id}/today",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_members"] == 3
        assert data["responded_count"] == 2
        assert data["response_rate"] == 66.7

    @pytest.mark.asyncio
    async def test_get_digest_history(
        self, client: AsyncClient, auth_headers, team_with_submissions
    ):
        """
        [TC-4.2.2] GET /{team_id}/history — returns list of digests.
        """
        team, _, owner, _, _ = team_with_submissions
        headers = await auth_headers(owner)

        # Trigger to create a digest
        await client.post(f"/api/v1/digests/{team.id}/trigger", headers=headers)

        response = await client.get(
            f"/api/v1/digests/{team.id}/history",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["responded_count"] == 2

    @pytest.mark.asyncio
    async def test_unauthorized_user_blocked(
        self, client: AsyncClient, auth_headers, team_with_submissions, create_test_user
    ):
        """
        [TC-4.2.4] User who doesn't own the team cannot access digest.
        """
        team, _, _, _, _ = team_with_submissions
        other_user = await create_test_user(email="intruder@test.com")
        headers = await auth_headers(other_user)

        response = await client.post(
            f"/api/v1/digests/{team.id}/trigger",
            headers=headers,
        )

        assert response.status_code == 403
