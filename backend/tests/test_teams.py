"""
StandupBot — Team Module Tests

Tests for team CRUD, member management, question management,
authorization checks, and plan limit enforcement.

COVERED TEST CASES (from test_cases.md):
  [TC-1.3.1] Create team with valid name, timezone, and questions
  [TC-1.3.2] Reject team creation with missing required fields
  [TC-1.3.3] List teams returns only teams owned by current user
  [TC-1.3.4] Update team settings (timezone, reminder time, questions)
  [TC-1.3.5] Delete team performs soft delete
  [TC-1.3.6] Enforce plan limits (free tier: 1 team max)
  [TC-1.4.1] Invite member by email — creates member record
  [TC-1.4.2] Reject duplicate member email within same team
  [TC-1.4.3] Remove member marks as inactive
  [TC-1.4.4] List members returns active members only
  [TC-1.4.5] Enforce plan limits (free tier: 5 members max)
"""

import pytest
from httpx import AsyncClient

from tests.conftest import make_auth_headers


# ═══════════════════════════════════════════════════════════════════════
# HELPERS — Create a team through the API (used by many tests)
# ═══════════════════════════════════════════════════════════════════════


async def _create_team_via_api(client: AsyncClient, name: str = "Test Team") -> dict:
    """Helper to create a team through the API and return the response data."""
    response = await client.post(
        "/api/v1/teams/",
        json={"name": name, "timezone": "America/New_York"},
    )
    assert response.status_code == 201, f"Team creation failed: {response.text}"
    return response.json()


async def _invite_member_via_api(
    client: AsyncClient, team_id: str, email: str = "member@example.com", name: str = "Member"
) -> dict:
    """Helper to invite a member and return the response data."""
    response = await client.post(
        f"/api/v1/teams/{team_id}/members",
        json={"email": email, "name": name},
    )
    assert response.status_code == 201, f"Invite failed: {response.text}"
    return response.json()


# ═══════════════════════════════════════════════════════════════════════
# POST /teams/ — Create Team Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCreateTeam:
    """Tests for POST /api/v1/teams/"""

    @pytest.mark.asyncio
    async def test_create_team_with_defaults(self, auth_client):
        """
        [TC-1.3.1] Create a team with just a name.
        Should auto-create 3 default questions and team settings.
        """
        client, user = auth_client

        response = await client.post(
            "/api/v1/teams/",
            json={"name": "Engineering Team"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Engineering Team"
        assert data["timezone"] == "UTC"  # Default
        assert data["is_active"] is True
        assert data["member_count"] == 0
        # Should have 3 default questions
        assert len(data["questions"]) == 3
        assert "accomplish yesterday" in data["questions"][0]["text"].lower()

    @pytest.mark.asyncio
    async def test_create_team_with_custom_questions(self, auth_client):
        """Create a team with custom questions."""
        client, _ = auth_client

        response = await client.post(
            "/api/v1/teams/",
            json={
                "name": "Design Team",
                "timezone": "Europe/London",
                "questions": [
                    {"text": "What designs did you finish?", "order_index": 0},
                    {"text": "What's in review?", "order_index": 1},
                ],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["timezone"] == "Europe/London"
        assert len(data["questions"]) == 2
        assert data["questions"][0]["text"] == "What designs did you finish?"

    @pytest.mark.asyncio
    async def test_create_team_missing_name_returns_422(self, auth_client):
        """
        [TC-1.3.2] Missing required field → 422.
        """
        client, _ = auth_client
        response = await client.post("/api/v1/teams/", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_team_unauthenticated_returns_401(self, client):
        """Creating a team without auth → 401."""
        response = await client.post(
            "/api/v1/teams/",
            json={"name": "Should Fail"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_team_plan_limit_free_tier(self, auth_client):
        """
        [TC-1.3.6] Free tier allows only 1 team.
        Creating a second team should return 403 PlanLimitError.
        """
        client, _ = auth_client

        # Create first team — should succeed
        await _create_team_via_api(client, "Team One")

        # Create second team — should fail
        response = await client.post(
            "/api/v1/teams/",
            json={"name": "Team Two"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "PLAN_LIMIT_EXCEEDED"


# ═══════════════════════════════════════════════════════════════════════
# GET /teams/ — List Teams Tests
# ═══════════════════════════════════════════════════════════════════════


class TestListTeams:
    """Tests for GET /api/v1/teams/"""

    @pytest.mark.asyncio
    async def test_list_teams_returns_own_teams(self, auth_client):
        """
        [TC-1.3.3] Should only return teams owned by the current user.
        """
        client, _ = auth_client

        # Create a team
        await _create_team_via_api(client, "My Team")

        # List teams
        response = await client.get("/api/v1/teams/")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Team"
        assert "member_count" in data[0]

    @pytest.mark.asyncio
    async def test_list_teams_empty(self, auth_client):
        """User with no teams gets an empty list."""
        client, _ = auth_client

        response = await client.get("/api/v1/teams/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_teams_excludes_deleted(self, auth_client):
        """Deleted (soft-deleted) teams should NOT appear in the list."""
        client, _ = auth_client

        team_data = await _create_team_via_api(client, "Will Be Deleted")

        # Delete the team
        await client.delete(f"/api/v1/teams/{team_data['id']}")

        # List should be empty
        response = await client.get("/api/v1/teams/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_teams_other_user_sees_nothing(self, client, create_test_user):
        """
        [TC-1.3.3] User B cannot see User A's teams.
        """
        # User A creates a team
        user_a = await create_test_user(email="usera@test.com")
        headers_a = make_auth_headers(user_a.id)
        await client.post(
            "/api/v1/teams/",
            json={"name": "Team A"},
            headers=headers_a,
        )

        # User B lists teams
        user_b = await create_test_user(email="userb@test.com")
        headers_b = make_auth_headers(user_b.id)
        response = await client.get("/api/v1/teams/", headers=headers_b)

        assert response.status_code == 200
        assert response.json() == []  # User B should see no teams


# ═══════════════════════════════════════════════════════════════════════
# GET /teams/{team_id} — Get Team Tests
# ═══════════════════════════════════════════════════════════════════════


class TestGetTeam:
    """Tests for GET /api/v1/teams/{team_id}"""

    @pytest.mark.asyncio
    async def test_get_team_returns_full_details(self, auth_client):
        """Get team includes questions and member count."""
        client, _ = auth_client

        team_data = await _create_team_via_api(client)

        response = await client.get(f"/api/v1/teams/{team_data['id']}")
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Test Team"
        assert "questions" in data
        assert len(data["questions"]) == 3

    @pytest.mark.asyncio
    async def test_get_team_not_owner_returns_403(self, client, create_test_user):
        """Accessing someone else's team → 403."""
        # User A creates a team
        user_a = await create_test_user(email="owner@test.com")
        headers_a = make_auth_headers(user_a.id)
        resp = await client.post(
            "/api/v1/teams/",
            json={"name": "Private Team"},
            headers=headers_a,
        )
        team_id = resp.json()["id"]

        # User B tries to access it
        user_b = await create_test_user(email="intruder@test.com")
        headers_b = make_auth_headers(user_b.id)
        response = await client.get(f"/api/v1/teams/{team_id}", headers=headers_b)

        assert response.status_code == 403
        assert response.json()["code"] == "AUTHORIZATION_ERROR"

    @pytest.mark.asyncio
    async def test_get_team_nonexistent_returns_404(self, auth_client):
        """Accessing a team that doesn't exist → 404."""
        client, _ = auth_client
        from uuid import uuid4

        response = await client.get(f"/api/v1/teams/{uuid4()}")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# PUT /teams/{team_id} — Update Team Tests
# ═══════════════════════════════════════════════════════════════════════


class TestUpdateTeam:
    """Tests for PUT /api/v1/teams/{team_id}"""

    @pytest.mark.asyncio
    async def test_update_team_partial(self, auth_client):
        """
        [TC-1.3.4] Partial update — only change the name, leave timezone intact.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        response = await client.put(
            f"/api/v1/teams/{team_data['id']}",
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        # Timezone should remain unchanged
        assert data["timezone"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_update_team_not_owner_returns_403(self, client, create_test_user):
        """Non-owner trying to update → 403."""
        user_a = await create_test_user(email="owner@test.com")
        headers_a = make_auth_headers(user_a.id)
        resp = await client.post(
            "/api/v1/teams/",
            json={"name": "Team A"},
            headers=headers_a,
        )
        team_id = resp.json()["id"]

        user_b = await create_test_user(email="other@test.com")
        headers_b = make_auth_headers(user_b.id)
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={"name": "Hacked Name"},
            headers=headers_b,
        )
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════
# DELETE /teams/{team_id} — Delete Team Tests
# ═══════════════════════════════════════════════════════════════════════


class TestDeleteTeam:
    """Tests for DELETE /api/v1/teams/{team_id}"""

    @pytest.mark.asyncio
    async def test_delete_team_soft_deletes(self, auth_client):
        """
        [TC-1.3.5] Delete should soft-delete (not hard-delete).
        The team disappears from list but data is preserved.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        response = await client.delete(f"/api/v1/teams/{team_data['id']}")
        assert response.status_code == 200
        assert response.json()["message"] == "Team deleted successfully"

        # Team should no longer appear in list
        list_resp = await client.get("/api/v1/teams/")
        assert list_resp.json() == []

        # Trying to access it directly should return 404
        get_resp = await client.get(f"/api/v1/teams/{team_data['id']}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_team_deactivates_members(self, auth_client):
        """Deleting a team should deactivate all its members."""
        client, _ = auth_client
        team_data = await _create_team_via_api(client)
        await _invite_member_via_api(client, team_data["id"], "bob@test.com", "Bob")

        # Delete the team
        await client.delete(f"/api/v1/teams/{team_data['id']}")

        # Members list should be inaccessible (team is deleted)
        response = await client.get(f"/api/v1/teams/{team_data['id']}/members")
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# POST /teams/{team_id}/members — Invite Member Tests
# ═══════════════════════════════════════════════════════════════════════


class TestInviteMember:
    """Tests for POST /api/v1/teams/{team_id}/members"""

    @pytest.mark.asyncio
    async def test_invite_member_success(self, auth_client):
        """
        [TC-1.4.1] Invite a member by email — should create a member record.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        response = await client.post(
            f"/api/v1/teams/{team_data['id']}/members",
            json={"email": "alice@example.com", "name": "Alice"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "alice@example.com"
        assert data["name"] == "Alice"
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_invite_duplicate_email_returns_409(self, auth_client):
        """
        [TC-1.4.2] Inviting the same email twice → 409 Conflict.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        # First invite works
        await _invite_member_via_api(client, team_data["id"], "alice@example.com")

        # Second invite with same email → conflict
        response = await client.post(
            f"/api/v1/teams/{team_data['id']}/members",
            json={"email": "alice@example.com", "name": "Alice Again"},
        )
        assert response.status_code == 409
        assert response.json()["code"] == "CONFLICT"

    @pytest.mark.asyncio
    async def test_invite_member_plan_limit(self, auth_client):
        """
        [TC-1.4.5] Free tier: max 5 members.
        6th invite should fail with PlanLimitError.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        # Invite 5 members (free limit)
        for i in range(5):
            await _invite_member_via_api(
                client, team_data["id"], f"member{i}@test.com", f"Member {i}"
            )

        # 6th should fail
        response = await client.post(
            f"/api/v1/teams/{team_data['id']}/members",
            json={"email": "member5@test.com", "name": "Member 5"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "PLAN_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_invite_member_not_owner_returns_403(self, client, create_test_user):
        """Non-owner can't invite members to a team they don't own."""
        user_a = await create_test_user(email="owner@test.com")
        headers_a = make_auth_headers(user_a.id)
        resp = await client.post(
            "/api/v1/teams/",
            json={"name": "Team A"},
            headers=headers_a,
        )
        team_id = resp.json()["id"]

        user_b = await create_test_user(email="notowner@test.com")
        headers_b = make_auth_headers(user_b.id)
        response = await client.post(
            f"/api/v1/teams/{team_id}/members",
            json={"email": "sneaky@test.com", "name": "Sneaky"},
            headers=headers_b,
        )
        assert response.status_code == 403


# ═══════════════════════════════════════════════════════════════════════
# GET /teams/{team_id}/members — List Members Tests
# ═══════════════════════════════════════════════════════════════════════


class TestListMembers:
    """Tests for GET /api/v1/teams/{team_id}/members"""

    @pytest.mark.asyncio
    async def test_list_members_returns_active_only(self, auth_client):
        """
        [TC-1.4.4] Only active members appear in the list.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        # Invite 2 members
        await _invite_member_via_api(client, team_data["id"], "alice@test.com", "Alice")
        bob = await _invite_member_via_api(client, team_data["id"], "bob@test.com", "Bob")

        # Remove Bob
        await client.delete(f"/api/v1/teams/{team_data['id']}/members/{bob['id']}")

        # List should only show Alice
        response = await client.get(f"/api/v1/teams/{team_data['id']}/members")
        assert response.status_code == 200
        members = response.json()
        assert len(members) == 1
        assert members[0]["email"] == "alice@test.com"

    @pytest.mark.asyncio
    async def test_list_members_empty_team(self, auth_client):
        """A team with no members returns an empty list."""
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        response = await client.get(f"/api/v1/teams/{team_data['id']}/members")
        assert response.status_code == 200
        assert response.json() == []


# ═══════════════════════════════════════════════════════════════════════
# DELETE /teams/{team_id}/members/{member_id} — Remove Member Tests
# ═══════════════════════════════════════════════════════════════════════


class TestRemoveMember:
    """Tests for DELETE /api/v1/teams/{team_id}/members/{member_id}"""

    @pytest.mark.asyncio
    async def test_remove_member_soft_removes(self, auth_client):
        """
        [TC-1.4.3] Remove sets is_active=False. Member data is preserved.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)
        member = await _invite_member_via_api(client, team_data["id"], "bob@test.com", "Bob")

        response = await client.delete(
            f"/api/v1/teams/{team_data['id']}/members/{member['id']}"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Member removed successfully"

    @pytest.mark.asyncio
    async def test_remove_nonexistent_member_returns_404(self, auth_client):
        """Removing a member that doesn't exist → 404."""
        client, _ = auth_client
        team_data = await _create_team_via_api(client)
        from uuid import uuid4

        response = await client.delete(
            f"/api/v1/teams/{team_data['id']}/members/{uuid4()}"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reinvite_removed_member_reactivates(self, auth_client):
        """
        Re-inviting a removed member should reactivate them (not create a duplicate).
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        # Invite, then remove
        member = await _invite_member_via_api(client, team_data["id"], "bob@test.com", "Bob")
        await client.delete(f"/api/v1/teams/{team_data['id']}/members/{member['id']}")

        # Re-invite same email
        response = await client.post(
            f"/api/v1/teams/{team_data['id']}/members",
            json={"email": "bob@test.com", "name": "Bob Reactivated"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["is_active"] is True
        assert data["name"] == "Bob Reactivated"

        # Should still have only 1 member in list
        list_resp = await client.get(f"/api/v1/teams/{team_data['id']}/members")
        assert len(list_resp.json()) == 1


# ═══════════════════════════════════════════════════════════════════════
# Question Management Tests
# ═══════════════════════════════════════════════════════════════════════


class TestQuestions:
    """Tests for GET/PUT /api/v1/teams/{team_id}/questions"""

    @pytest.mark.asyncio
    async def test_get_questions_returns_defaults(self, auth_client):
        """New team should have 3 default questions."""
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        response = await client.get(f"/api/v1/teams/{team_data['id']}/questions")
        assert response.status_code == 200
        questions = response.json()
        assert len(questions) == 3

    @pytest.mark.asyncio
    async def test_update_questions_replaces_all(self, auth_client):
        """
        [TC-1.3.4] Updating questions replaces the old set entirely.
        """
        client, _ = auth_client
        team_data = await _create_team_via_api(client)

        response = await client.put(
            f"/api/v1/teams/{team_data['id']}/questions",
            json=[
                {"text": "New Q1", "order_index": 0},
                {"text": "New Q2", "order_index": 1},
            ],
        )
        assert response.status_code == 200
        questions = response.json()
        assert len(questions) == 2
        assert questions[0]["text"] == "New Q1"

        # Verify old questions are gone from the active list
        get_resp = await client.get(f"/api/v1/teams/{team_data['id']}/questions")
        assert len(get_resp.json()) == 2
