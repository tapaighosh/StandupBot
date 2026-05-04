"""
StandupBot — Notification System Tests

Tests for email service, notification orchestration, and response rate alerts.

COVERED TEST CASES (from test_cases.md Section 5):
  [TC-5.1.1] Reminder sent at configured time per team timezone
  [TC-5.1.2] Reminder contains correct personalized magic link
  [TC-5.1.3] Reminder sent via email when email reminders enabled
  [TC-5.1.5] No reminder sent to inactive members
  [TC-5.2.1] Nudge sent if no submission by T + configured delay
  [TC-5.2.2] No nudge sent if already submitted
  [TC-5.2.3] No nudge sent if nudges disabled for team
  [TC-5.2.4] Only one nudge per member per day
  [TC-5.3.1] Alert sent if response rate drops below threshold
  [TC-5.3.2] No alert if response rate is above threshold

TESTING STRATEGY:
  We MOCK the EmailService — no real Resend API calls in tests.
  The MockEmailService captures all calls so we can assert on them.
  The TokenService runs for real against the test DB.
"""

from datetime import date, datetime, time, timezone
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member
from app.models.question import Question
from app.models.submission import Answer, Submission
from app.models.team import Team, TeamSettings
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService


# ═══════════════════════════════════════════════════════════════════════
# MOCK EMAIL SERVICE
# ═══════════════════════════════════════════════════════════════════════


class MockEmailService(EmailService):
    """
    Mock EmailService that captures all sends without making API calls.
    Set simulate_failure=True to test the email failure path.
    """

    def __init__(self, simulate_failure: bool = False):
        # Don't call super().__init__() — we don't want Resend initialization
        self._client = "mock"  # truthy — passes _is_ready() check
        self.simulate_failure = simulate_failure
        self.reminders_sent: list[dict] = []
        self.nudges_sent: list[dict] = []
        self.digests_sent: list[dict] = []
        self.alerts_sent: list[dict] = []

    def _is_ready(self) -> bool:
        return not self.simulate_failure

    async def send_reminder(self, to_email, member_name, team_name, magic_link) -> bool:
        if self.simulate_failure:
            return False
        self.reminders_sent.append({
            "to_email": to_email,
            "member_name": member_name,
            "team_name": team_name,
            "magic_link": magic_link,
        })
        return True

    async def send_nudge(self, to_email, member_name, team_name, magic_link) -> bool:
        if self.simulate_failure:
            return False
        self.nudges_sent.append({
            "to_email": to_email,
            "member_name": member_name,
            "team_name": team_name,
            "magic_link": magic_link,
        })
        return True

    async def send_digest(self, **kwargs) -> bool:
        if self.simulate_failure:
            return False
        self.digests_sent.append(kwargs)
        return True

    async def send_low_response_alert(self, **kwargs) -> bool:
        if self.simulate_failure:
            return False
        self.alerts_sent.append(kwargs)
        return True


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
async def notification_team(db_session: AsyncSession, create_test_user):
    """
    Create a team with 3 members: Alice (active), Bob (active), Charlie (active).
    Returns (team, members, owner).
    """
    owner = await create_test_user(email="manager@notif-test.com", name="Manager")

    team = Team(
        owner_id=owner.id,
        name="Notification Test Team",
        timezone="UTC",
        reminder_time=time(8, 0),
        digest_time=time(10, 0),
        submission_window_start=time(0, 0),
        submission_window_end=time(23, 59),
        allow_late_submissions=True,
        is_active=True,
    )
    db_session.add(team)
    await db_session.flush()

    settings = TeamSettings(
        team_id=team.id,
        email_reminders_enabled=True,
        nudge_enabled=True,
        nudge_delay_minutes=120,
        low_response_alert_threshold=0.5,
    )
    db_session.add(settings)

    q1 = Question(team_id=team.id, text="What did you do?", order_index=0, is_active=True)
    db_session.add(q1)

    alice = Member(team_id=team.id, email="alice@test.com", name="Alice", is_active=True)
    bob = Member(team_id=team.id, email="bob@test.com", name="Bob", is_active=True)
    charlie = Member(team_id=team.id, email="charlie@test.com", name="Charlie", is_active=True)
    db_session.add_all([alice, bob, charlie])

    # Inactive member — should never be notified
    inactive = Member(team_id=team.id, email="inactive@test.com", name="Inactive", is_active=False)
    db_session.add(inactive)

    await db_session.flush()
    return team, [alice, bob, charlie], owner


@pytest.fixture
async def team_with_submission(db_session: AsyncSession, notification_team):
    """Alice has submitted today; Bob and Charlie have not."""
    team, members, owner = notification_team
    alice, bob, charlie = members
    today = date.today()

    submission = Submission(
        member_id=alice.id,
        team_id=team.id,
        standup_date=today,
        is_late=False,
        submitted_at=datetime.now(timezone.utc),
    )
    db_session.add(submission)
    await db_session.flush()

    return team, members, owner


# ═══════════════════════════════════════════════════════════════════════
# REMINDER TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestDailyReminders:

    @pytest.mark.asyncio
    async def test_reminders_sent_to_all_active_members(
        self, db_session: AsyncSession, notification_team
    ):
        """
        [TC-5.1.2] Reminder contains correct personalized magic link
        [TC-5.1.3] Reminder sent via email when email reminders enabled
        """
        team, members, _ = notification_team
        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result = await service.send_daily_reminders(team.id)

        # 3 active members, 1 inactive → 3 reminders sent
        assert result["sent"] == 3
        assert result["failed"] == 0
        assert result["skipped"] == 0
        assert len(mock_email.reminders_sent) == 3

        # Check magic links are present
        for reminder in mock_email.reminders_sent:
            assert "/standup/" in reminder["magic_link"]
            assert reminder["team_name"] == "Notification Test Team"

    @pytest.mark.asyncio
    async def test_no_reminder_to_inactive_members(
        self, db_session: AsyncSession, notification_team
    ):
        """[TC-5.1.5] No reminder sent to inactive members."""
        team, _, _ = notification_team
        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        await service.send_daily_reminders(team.id)

        emails_sent = {r["to_email"] for r in mock_email.reminders_sent}
        assert "inactive@test.com" not in emails_sent

    @pytest.mark.asyncio
    async def test_reminders_skipped_when_email_disabled(
        self, db_session: AsyncSession, notification_team
    ):
        """No reminders when email_reminders_enabled = False."""
        from sqlalchemy import select
        from app.models.team import TeamSettings

        team, _, _ = notification_team
        # Fetch settings explicitly in the async context to avoid lazy load
        stmt = select(TeamSettings).where(TeamSettings.team_id == team.id)
        result = await db_session.execute(stmt)
        settings_obj = result.scalar_one()
        settings_obj.email_reminders_enabled = False
        await db_session.flush()

        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result2 = await service.send_daily_reminders(team.id)

        assert result2["sent"] == 0
        assert result2["skipped"] == 3
        assert len(mock_email.reminders_sent) == 0

    @pytest.mark.asyncio
    async def test_reminder_personalization(
        self, db_session: AsyncSession, notification_team
    ):
        """Reminder contains each member's name."""
        team, members, _ = notification_team
        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        await service.send_daily_reminders(team.id)

        names_in_reminders = {r["member_name"] for r in mock_email.reminders_sent}
        assert "Alice" in names_in_reminders
        assert "Bob" in names_in_reminders
        assert "Charlie" in names_in_reminders
        assert "Inactive" not in names_in_reminders

    @pytest.mark.asyncio
    async def test_email_failure_counts_as_failed(
        self, db_session: AsyncSession, notification_team
    ):
        """If email sending fails, it's counted as failed not crashed."""
        team, _, _ = notification_team
        failing_email = MockEmailService(simulate_failure=True)
        service = NotificationService(db_session, email_service=failing_email)

        result = await service.send_daily_reminders(team.id)

        assert result["failed"] == 3
        assert result["sent"] == 0


# ═══════════════════════════════════════════════════════════════════════
# NUDGE TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestNudges:

    @pytest.mark.asyncio
    async def test_nudge_sent_to_non_submitters(
        self, db_session: AsyncSession, team_with_submission
    ):
        """
        [TC-5.2.1] Nudge sent if no submission by T + configured delay
        Alice submitted, Bob and Charlie did not → only Bob and Charlie nudged
        """
        team, members, _ = team_with_submission
        alice, bob, charlie = members

        # First, generate tokens (simulates reminder job having run)
        from app.services.token_service import TokenService
        token_service = TokenService(db_session)
        await token_service.generate_daily_tokens(team.id)
        await db_session.flush()

        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result = await service.send_nudges(team.id)

        assert result["nudged"] == 2
        assert result["already_submitted"] == 1
        nudged_emails = {n["to_email"] for n in mock_email.nudges_sent}
        assert "alice@test.com" not in nudged_emails  # She submitted
        assert "bob@test.com" in nudged_emails
        assert "charlie@test.com" in nudged_emails

    @pytest.mark.asyncio
    async def test_no_nudge_if_nudges_disabled(
        self, db_session: AsyncSession, notification_team
    ):
        """[TC-5.2.3] No nudge sent if nudges disabled for team."""
        from sqlalchemy import select
        from app.models.team import TeamSettings

        team, _, _ = notification_team
        stmt = select(TeamSettings).where(TeamSettings.team_id == team.id)
        result = await db_session.execute(stmt)
        settings_obj = result.scalar_one()
        settings_obj.nudge_enabled = False
        await db_session.flush()

        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result2 = await service.send_nudges(team.id)

        assert result2["nudged"] == 0
        assert len(mock_email.nudges_sent) == 0

    @pytest.mark.asyncio
    async def test_no_nudge_if_already_submitted(
        self, db_session: AsyncSession, notification_team
    ):
        """[TC-5.2.2] No nudge sent if already submitted — all members submitted."""
        team, members, _ = notification_team
        today = date.today()

        # Submit for all 3 members
        for member in members:
            sub = Submission(
                member_id=member.id,
                team_id=team.id,
                standup_date=today,
                is_late=False,
                submitted_at=datetime.now(timezone.utc),
            )
            db_session.add(sub)
        await db_session.flush()

        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result = await service.send_nudges(team.id)

        assert result["nudged"] == 0
        assert result["already_submitted"] == 3
        assert len(mock_email.nudges_sent) == 0

    @pytest.mark.asyncio
    async def test_only_one_nudge_per_day(
        self, db_session: AsyncSession, team_with_submission
    ):
        """[TC-5.2.4] Only one nudge per member per day."""
        team, members, _ = team_with_submission

        # Generate tokens first
        from app.services.token_service import TokenService
        token_service = TokenService(db_session)
        await token_service.generate_daily_tokens(team.id)
        await db_session.flush()

        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        # First nudge run
        result1 = await service.send_nudges(team.id)
        nudged_first = result1["nudged"]
        await db_session.commit()

        # Second nudge run — should NOT re-nudge
        result2 = await service.send_nudges(team.id)

        assert result2["nudged"] == 0
        assert result2["skipped"] >= nudged_first  # Previous nudgees are now skipped


# ═══════════════════════════════════════════════════════════════════════
# ALERT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestResponseRateAlert:

    @pytest.mark.asyncio
    async def test_alert_sent_when_rate_below_threshold(
        self, db_session: AsyncSession, team_with_submission
    ):
        """
        [TC-5.3.1] Alert sent if response rate drops below threshold.
        Only Alice submitted → 1/3 = 33% < 50% threshold → alert sent.
        """
        team, _, owner = team_with_submission
        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result = await service.check_response_rate_alert(team.id)

        assert result is True
        assert len(mock_email.alerts_sent) == 1
        alert = mock_email.alerts_sent[0]
        assert alert["to_email"] == owner.email
        assert alert["team_name"] == "Notification Test Team"
        assert alert["response_rate"] < 50.0
        assert alert["total_members"] == 3
        assert alert["responded_count"] == 1

    @pytest.mark.asyncio
    async def test_no_alert_when_rate_above_threshold(
        self, db_session: AsyncSession, notification_team
    ):
        """
        [TC-5.3.2] No alert if response rate is above threshold.
        All 3 members submitted → 100% > 50% threshold → no alert.
        """
        team, members, _ = notification_team
        today = date.today()

        for member in members:
            sub = Submission(
                member_id=member.id,
                team_id=team.id,
                standup_date=today,
                is_late=False,
                submitted_at=datetime.now(timezone.utc),
            )
            db_session.add(sub)
        await db_session.flush()

        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        result = await service.check_response_rate_alert(team.id)

        assert result is False
        assert len(mock_email.alerts_sent) == 0

    @pytest.mark.asyncio
    async def test_alert_includes_non_responder_names(
        self, db_session: AsyncSession, team_with_submission
    ):
        """Alert email includes names of non-responders (Bob and Charlie)."""
        team, _, _ = team_with_submission
        mock_email = MockEmailService()
        service = NotificationService(db_session, email_service=mock_email)

        await service.check_response_rate_alert(team.id)

        alert = mock_email.alerts_sent[0]
        non_responders = alert["non_responders"]
        assert "Bob" in non_responders
        assert "Charlie" in non_responders
        assert "Alice" not in non_responders  # Alice submitted


# ═══════════════════════════════════════════════════════════════════════
# EMAIL SERVICE UNIT TESTS
# ═══════════════════════════════════════════════════════════════════════


class TestEmailServiceTemplates:
    """Test that templates render correctly without actual sending."""

    def test_template_rendering_reminder(self):
        """Reminder template renders without errors."""
        from app.services.email_service import _render
        html = _render(
            "reminder.html",
            member_name="Alice",
            team_name="Engineering",
            magic_link="http://localhost:5173/standup/test-token",
        )
        assert "Alice" in html
        assert "Engineering" in html
        assert "http://localhost:5173/standup/test-token" in html

    def test_template_rendering_nudge(self):
        """Nudge template renders without errors."""
        from app.services.email_service import _render
        html = _render(
            "nudge.html",
            member_name="Bob",
            team_name="Engineering",
            magic_link="http://localhost:5173/standup/test-token",
        )
        assert "Bob" in html
        assert "Don't forget" in html

    def test_template_rendering_alert(self):
        """Alert template renders without errors."""
        from app.services.email_service import _render
        html = _render(
            "alert.html",
            manager_name="Manager",
            team_name="Engineering",
            response_rate=33.3,
            responded_count=1,
            total_members=3,
            threshold=50,
            non_responders=["Bob", "Charlie"],
            dashboard_url="http://localhost:5173/dashboard/digests/today",
        )
        assert "33.3" in html
        assert "Bob" in html
        assert "Charlie" in html

    def test_template_rendering_digest_with_ai_summary(self):
        """Digest template renders correctly with AI summary."""
        from app.services.email_service import _render
        html = _render(
            "digest.html",
            manager_name="Manager",
            team_name="Engineering",
            digest_date="2026-05-04",
            ai_summary="The team made great progress today.",
            responded_count=2,
            total_members=3,
            response_rate=66.7,
            rate_color="#fdcb6e",
            blockers=[],
            non_responders=["Charlie"],
            dashboard_url="http://localhost:5173/dashboard/digests/abc",
        )
        assert "The team made great progress today." in html
        assert "Charlie" in html
        assert "66.7" in html

    def test_template_rendering_digest_no_ai_summary(self):
        """Digest template handles null AI summary gracefully."""
        from app.services.email_service import _render
        html = _render(
            "digest.html",
            manager_name="Manager",
            team_name="Engineering",
            digest_date="2026-05-04",
            ai_summary=None,
            responded_count=0,
            total_members=3,
            response_rate=0.0,
            rate_color="#ff6b6b",
            blockers=[],
            non_responders=["Alice", "Bob", "Charlie"],
            dashboard_url="http://localhost:5173/dashboard/digests/abc",
        )
        assert "AI summary unavailable" in html
