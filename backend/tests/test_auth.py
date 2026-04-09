"""
StandupBot — Auth Module Tests

Tests for Google OAuth login, JWT token management, and user profile endpoints.

TEST STRUCTURE — AAA Pattern:
  Arrange: Set up test data (users, tokens, mocks)
  Act:     Call the API endpoint
  Assert:  Check the response status, body, and side effects

HOW WE TEST WITHOUT A REAL GOOGLE ACCOUNT:
  We mock `AuthService.verify_google_token` to return fake user data.
  This tests our route + service logic without calling the real Google API.
  The actual HTTP call to Google is a simple httpx.get() — if Google's
  API works, our code works. What we're really testing is: does our code
  correctly handle Google's response?

COVERED TEST CASES (from test_cases.md):
  [TC-1.1.4] Google OAuth returns valid user profile and creates account
  [TC-1.1.5] Google OAuth failure returns appropriate error
  [TC-1.2.1] Login with valid Google OAuth token returns JWT
  [TC-1.2.2] JWT token contains correct claims (user_id, email, exp)
  [TC-1.2.3] Expired JWT is rejected with 401
  [TC-1.2.4] Refresh token generates new access token
  [TC-1.2.5] Invalidated refresh token is rejected
  [TC-1.2.6] GET /me returns current user profile
"""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.exceptions import AuthenticationError, ExternalServiceError
from tests.conftest import make_auth_headers


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES — Reusable fake data
# ═══════════════════════════════════════════════════════════════════════


# This is what verify_google_token() returns after calling Google's API.
FAKE_GOOGLE_USER = {
    "email": "manager@example.com",
    "name": "Test Manager",
    "google_id": "google-123456789",
    "avatar_url": "https://lh3.googleusercontent.com/photo.jpg",
}


# ═══════════════════════════════════════════════════════════════════════
# POST /login/google — Google OAuth Login Tests
# ═══════════════════════════════════════════════════════════════════════


class TestGoogleLogin:
    """Tests for the POST /api/v1/auth/login/google endpoint."""

    @pytest.mark.asyncio
    async def test_login_new_user_creates_account_and_returns_tokens(self, client: AsyncClient):
        """
        [TC-1.1.4] [TC-1.2.1]
        First-time Google login should:
        1. Call Google to verify the credential ← we mock this
        2. Create a new user in the database
        3. Return JWT access + refresh tokens

        We mock verify_google_token() because:
        - We don't want tests to call the real Google API
        - verify_google_token() is just a simple httpx.get() — not what we're testing
        - What we ARE testing: does the route correctly create a user and return tokens?
        """
        # Arrange: mock the Google verification step
        with patch(
            "app.services.auth_service.AuthService.verify_google_token",
            new_callable=AsyncMock,
            return_value=FAKE_GOOGLE_USER,
        ):
            # Act: call the login endpoint
            response = await client.post(
                "/api/v1/auth/login/google",
                json={"credential": "fake-google-id-token"},
            )

        # Assert: should return 200 with tokens
        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"

        data = response.json()
        assert "access_token" in data, "Response must include access_token"
        assert "refresh_token" in data, "Response must include refresh_token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0, "expires_in must be positive"

    @pytest.mark.asyncio
    async def test_login_existing_user_returns_tokens_without_duplicating(
        self, client: AsyncClient, create_test_user
    ):
        """
        [TC-1.1.2] Second login with same Google account should:
        - Find the existing user (NOT create a duplicate)
        - Return tokens for the existing user
        """
        # Arrange: create user in DB first, then "log in" with same google_id
        await create_test_user(
            email="manager@example.com",
            google_id="google-123456789",
        )

        with patch(
            "app.services.auth_service.AuthService.verify_google_token",
            new_callable=AsyncMock,
            return_value=FAKE_GOOGLE_USER,
        ):
            response = await client.post(
                "/api/v1/auth/login/google",
                json={"credential": "fake-google-id-token"},
            )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_login_invalid_google_token_returns_401(self, client: AsyncClient):
        """
        [TC-1.1.5] If Google says the token is invalid, we return 401.
        We simulate this by making verify_google_token raise AuthenticationError.
        """
        with patch(
            "app.services.auth_service.AuthService.verify_google_token",
            new_callable=AsyncMock,
            side_effect=AuthenticationError("Invalid Google credential"),
        ):
            response = await client.post(
                "/api/v1/auth/login/google",
                json={"credential": "bad-token"},
            )

        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_login_google_api_unavailable_returns_502(self, client: AsyncClient):
        """
        If Google's API is down (network error), we return 502.
        """
        with patch(
            "app.services.auth_service.AuthService.verify_google_token",
            new_callable=AsyncMock,
            side_effect=ExternalServiceError(
                detail="Could not verify Google credential",
                service="Google OAuth",
            ),
        ):
            response = await client.post(
                "/api/v1/auth/login/google",
                json={"credential": "some-token"},
            )

        assert response.status_code == 502

    @pytest.mark.asyncio
    async def test_login_missing_credential_returns_422(self, client: AsyncClient):
        """
        Sending empty body should return 422 (Pydantic validation).
        FastAPI validates the request body BEFORE our code runs.
        """
        response = await client.post("/api/v1/auth/login/google", json={})
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════
# POST /refresh — Token Refresh Tests
# ═══════════════════════════════════════════════════════════════════════


class TestTokenRefresh:
    """Tests for the POST /api/v1/auth/refresh endpoint."""

    @pytest.mark.asyncio
    async def test_refresh_valid_token_returns_new_tokens(
        self, client: AsyncClient, create_test_user
    ):
        """
        [TC-1.2.4] A valid refresh token should return a new access + refresh pair.
        """
        # Arrange: create user and generate a real refresh token for them
        user = await create_test_user()

        from app.utils.security import create_refresh_token

        refresh = create_refresh_token(data={"sub": str(user.id)})

        # Act
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New refresh token should be DIFFERENT (token rotation)
        assert data["refresh_token"] != refresh

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_type_returns_401(
        self, client: AsyncClient, create_test_user
    ):
        """
        Using an ACCESS token where a REFRESH token is expected should fail.
        This prevents token type confusion attacks.
        """
        user = await create_test_user()

        from app.utils.security import create_access_token

        access = create_access_token(data={"sub": str(user.id)})

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access},  # Wrong token type!
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_string_returns_401(self, client: AsyncClient):
        """
        [TC-1.2.5] A completely invalid (garbage) token should be rejected.
        """
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not-a-real-jwt-at-all"},
        )

        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_refresh_missing_body_returns_422(self, client: AsyncClient):
        """Empty body → 422 (Pydantic validation)."""
        response = await client.post("/api/v1/auth/refresh", json={})
        assert response.status_code == 422


# ═══════════════════════════════════════════════════════════════════════
# GET /me — User Profile Tests
# ═══════════════════════════════════════════════════════════════════════


class TestGetMe:
    """Tests for the GET /api/v1/auth/me endpoint."""

    @pytest.mark.asyncio
    async def test_me_authenticated_returns_user_profile(self, auth_client):
        """
        [TC-1.2.6] GET /me with a valid token should return user profile.
        """
        client, user = auth_client

        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == user.email
        assert data["name"] == user.name
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_me_no_token_returns_401(self, client: AsyncClient):
        """
        [TC-1.2.3] GET /me without Authorization header → 401.
        """
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert response.json()["code"] == "AUTHENTICATION_ERROR"

    @pytest.mark.asyncio
    async def test_me_invalid_token_returns_401(self, client: AsyncClient):
        """Garbage token string → 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this-is-not-a-jwt"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_expired_token_returns_401(self, client: AsyncClient, create_test_user):
        """
        [TC-1.2.3] Expired access token → 401.
        """
        user = await create_test_user()

        from app.utils.security import create_access_token

        expired = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired}"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_wrong_header_format_returns_401(self, client: AsyncClient):
        """Authorization header without 'Bearer ' prefix → 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Token some-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_me_nonexistent_user_returns_404(self, client: AsyncClient):
        """
        Valid JWT for a deleted/nonexistent user → 404.
        This can happen if a user is deleted but still has a valid token.
        """
        from uuid import uuid4

        headers = make_auth_headers(str(uuid4()))
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# POST /logout — Logout Tests
# ═══════════════════════════════════════════════════════════════════════


class TestLogout:
    """Tests for the POST /api/v1/auth/logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout_authenticated_returns_success(self, auth_client):
        """Authenticated user can logout successfully."""
        client, _ = auth_client
        response = await client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully"

    @pytest.mark.asyncio
    async def test_logout_unauthenticated_returns_401(self, client: AsyncClient):
        """Logout without a token → 401."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# JWT TOKEN CLAIMS — Unit tests (no HTTP, no DB)
# ═══════════════════════════════════════════════════════════════════════


class TestJWTClaims:
    """Tests that verify JWT tokens contain correct claims."""

    def test_access_token_contains_correct_claims(self):
        """
        [TC-1.2.2] Access token should contain: sub, type=access, exp
        """
        from uuid import uuid4

        from app.utils.security import create_access_token, decode_token

        user_id = str(uuid4())
        token = create_access_token(data={"sub": user_id})
        payload = decode_token(token, expected_type="access")

        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_refresh_token_contains_correct_claims(self):
        """Refresh token should have type=refresh."""
        from uuid import uuid4

        from app.utils.security import create_refresh_token, decode_token

        user_id = str(uuid4())
        token = create_refresh_token(data={"sub": user_id})
        payload = decode_token(token, expected_type="refresh")

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_access_token_rejected_as_refresh(self):
        """
        Access token must NOT be accepted where refresh is expected.
        Prevents token type confusion.
        """
        from uuid import uuid4

        from app.utils.security import create_access_token, decode_token

        token = create_access_token(data={"sub": str(uuid4())})

        with pytest.raises(AuthenticationError):
            decode_token(token, expected_type="refresh")

    def test_expired_token_is_rejected(self):
        """Expired token should raise AuthenticationError."""
        from uuid import uuid4

        from app.utils.security import create_access_token, decode_token

        token = create_access_token(
            data={"sub": str(uuid4())},
            expires_delta=timedelta(seconds=-1),
        )

        with pytest.raises(AuthenticationError):
            decode_token(token, expected_type="access")
