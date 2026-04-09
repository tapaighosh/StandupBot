"""
StandupBot — Auth Service

Handles Google OAuth verification, user creation, and JWT token management.

HOW IT WORKS:
1. Manager clicks "Sign in with Google" on the frontend.
2. Google returns a `credential` (an ID token — a JWT signed by Google).
3. We send that credential to Google's tokeninfo endpoint to verify it.
4. Google responds with the user's email, name, and google_id.
5. We look up the user in our DB by google_id:
   - If found → existing user. Return them.
   - If not found → create a new User row.
6. We generate our OWN JWT tokens (access + refresh) and return them.
7. The frontend stores these tokens and sends them in the Authorization header.

KEY CONCEPTS:
- `verify_google_token()`: Asks Google "is this credential real?"
- `find_or_create_user()`: Upsert pattern — find or create
- `generate_tokens()`: Creates our own JWTs (NOT Google's tokens)
- `decode_token()` in security.py: Validates our JWTs on every request
"""

import logging
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import AuthenticationError, ExternalServiceError, NotFoundError
from app.models.user import User
from app.utils.security import create_access_token, create_refresh_token, decode_token

logger = logging.getLogger("standupbot.services.auth")


class AuthService:
    """
    Service for authentication and user management.

    All methods are async because they talk to the database (I/O bound).
    The `db` parameter is an async SQLAlchemy session injected by FastAPI.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ──────────────────────────────────────────────────────────────────────
    # 1. VERIFY GOOGLE TOKEN
    # ──────────────────────────────────────────────────────────────────────

    async def verify_google_token(self, credential: str) -> dict:
        """
        Verify a Google OAuth credential (ID token) by asking Google.

        HOW IT WORKS:
        - The frontend gets a `credential` string from Google Identity Services.
        - That credential is actually a JWT signed by Google.
        - We send it to Google's `tokeninfo` endpoint for verification.
        - Google checks the signature and returns the user info.

        WHY NOT VERIFY LOCALLY?
        - We could decode the JWT ourselves using Google's public keys,
          but calling tokeninfo is simpler, always up-to-date, and handles
          key rotation automatically. Good enough for an MVP.

        Args:
            credential: The ID token string from Google's frontend SDK.

        Returns:
            dict with keys: email, name, google_id, avatar_url

        Raises:
            AuthenticationError: If Google says the token is invalid.
            ExternalServiceError: If Google's API is unreachable.
        """
        try:
            # httpx is an async HTTP client (like requests, but async)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": credential},
                    timeout=10.0,  # Don't hang forever if Google is slow
                )

            # Google returns 200 for valid tokens, 400+ for invalid
            if response.status_code != 200:
                logger.warning(f"Google token verification failed: {response.status_code}")
                raise AuthenticationError("Invalid Google credential")

            data = response.json()

            # SECURITY CHECK: Verify the token was meant for OUR app.
            # Without this check, anyone with a valid Google token from
            # a different app could log in to ours!
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                logger.warning(
                    f"Google token audience mismatch: got {data.get('aud')}, "
                    f"expected {settings.GOOGLE_CLIENT_ID}"
                )
                raise AuthenticationError("Token was not issued for this application")

            # Extract the fields we care about
            return {
                "email": data["email"],
                "name": data.get("name", data["email"].split("@")[0]),
                "google_id": data["sub"],  # Google's unique user ID
                "avatar_url": data.get("picture"),
            }

        except httpx.HTTPError as e:
            # Network error — Google is unreachable
            logger.error(f"Google API request failed: {e}")
            raise ExternalServiceError(
                detail="Could not verify Google credential",
                service="Google OAuth",
            )

    # ──────────────────────────────────────────────────────────────────────
    # 2. FIND OR CREATE USER
    # ──────────────────────────────────────────────────────────────────────

    async def find_or_create_user(self, google_user: dict) -> User:
        """
        Find an existing user by google_id, or create a new one.

        This is an "upsert" pattern: we try to find first, create only if needed.

        WHY google_id AND NOT email?
        - A user could change their Google email address. The google_id
          (the `sub` field) never changes — it's the stable identifier.
        - We also check email as a fallback for safety.

        Args:
            google_user: Dict from verify_google_token() with email, name, etc.

        Returns:
            The User SQLAlchemy model instance (new or existing).
        """
        google_id = google_user["google_id"]
        email = google_user["email"]

        # Try to find by google_id first (primary lookup)
        stmt = select(User).where(User.google_id == google_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # User exists! Update their profile info in case it changed
            # (Google name/avatar can change over time)
            user.name = google_user["name"]
            user.avatar_url = google_user.get("avatar_url")
            # Re-activate if previously deactivated
            if not user.is_active:
                user.is_active = True
            logger.info(f"Existing user login: {email}")
            return user

        # Check if there's a user with the same email but no google_id
        # (could happen if we add other auth methods later)
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        existing_by_email = result.scalar_one_or_none()

        if existing_by_email:
            # Link the Google account to the existing user
            existing_by_email.google_id = google_id
            existing_by_email.name = google_user["name"]
            existing_by_email.avatar_url = google_user.get("avatar_url")
            logger.info(f"Linked Google account to existing user: {email}")
            return existing_by_email

        # No user exists — create a brand new one
        new_user = User(
            email=email,
            name=google_user["name"],
            google_id=google_id,
            avatar_url=google_user.get("avatar_url"),
            is_active=True,
        )
        self.db.add(new_user)

        # Flush to get the generated UUID (but don't commit yet —
        # the commit happens in the database.py session handler)
        await self.db.flush()

        logger.info(f"New user created: {email} (id={new_user.id})")
        return new_user

    # ──────────────────────────────────────────────────────────────────────
    # 3. GENERATE TOKENS
    # ──────────────────────────────────────────────────────────────────────

    async def generate_tokens(self, user_id: UUID) -> dict:
        """
        Generate JWT access and refresh tokens for a user.

        TWO TOKENS, WHY?
        - Access token: Short-lived (30 min). Sent with every API request.
          If stolen, it expires quickly — limited damage.
        - Refresh token: Long-lived (7 days). Only sent to POST /refresh.
          Used to get a new access token without re-logging in.

        This is the standard OAuth2 pattern used by most APIs.

        Args:
            user_id: The UUID of the authenticated user.

        Returns:
            dict: { access_token, refresh_token, token_type, expires_in }
        """
        # The "sub" (subject) claim is the standard JWT field for "who is this token for?"
        token_data = {"sub": str(user_id)}

        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data=token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # In seconds
        }

    # ──────────────────────────────────────────────────────────────────────
    # 4. REFRESH ACCESS TOKEN
    # ──────────────────────────────────────────────────────────────────────

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Validate a refresh token and generate a new access token.

        HOW IT WORKS:
        1. Decode the refresh token JWT and verify:
           - Signature is valid (not tampered)
           - Not expired
           - Type is "refresh" (not an access token being reused)
        2. Check that the user still exists and is active
        3. Generate new access + refresh tokens (token rotation)

        WHY ROTATE BOTH TOKENS?
        - If a refresh token is stolen, the real user will try to use it too.
        - When both try to use the same refresh token, one will fail.
        - By issuing a new refresh token each time, a stolen token becomes
          a one-time-use attack vector.

        Args:
            refresh_token: The refresh JWT string from the client.

        Returns:
            dict: { access_token, refresh_token, token_type, expires_in }

        Raises:
            AuthenticationError: If the refresh token is invalid/expired.
            NotFoundError: If the user no longer exists.
        """
        # decode_token() will raise AuthenticationError if invalid
        payload = decode_token(refresh_token, expected_type="refresh")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token: missing user ID")

        # Make sure the user still exists and is active
        user = await self.get_user_by_id(user_id)
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        # Generate fresh tokens (token rotation)
        return await self.generate_tokens(user.id)

    # ──────────────────────────────────────────────────────────────────────
    # 5. GET USER BY ID
    # ──────────────────────────────────────────────────────────────────────

    async def get_user_by_id(self, user_id: str | UUID) -> User:
        """
        Fetch a user from the database by their ID.

        This is used by:
        - The /me endpoint (to return the current user's profile)
        - The refresh_access_token method (to verify the user still exists)
        - Any dependency that needs to load the full user object

        Args:
            user_id: UUID or string UUID of the user.

        Returns:
            User model instance.

        Raises:
            NotFoundError: If no user exists with this ID.
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise NotFoundError(resource="User")

        return user

