"""
StandupBot — Auth API Routes

Handles Google OAuth login, token refresh, logout, and user profile.

ARCHITECTURE PATTERN — "Thin Routes, Fat Services":
- Routes handle HTTP concerns only: parse request, call service, return response.
- Business logic lives in AuthService (services/auth_service.py).
- This makes the service layer testable independently of HTTP/FastAPI.

ROUTE SUMMARY:
  POST /login/google  →  Verify Google token → create/find user → return JWTs
  POST /refresh       →  Validate refresh token → return new JWTs
  POST /logout        →  Client-side only (clear tokens)
  GET  /me            →  Return current user's profile (requires auth)
"""

import logging

from fastapi import APIRouter

from app.dependencies import CurrentUserId, DBSession
from app.schemas.auth import (
    GoogleAuthRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

logger = logging.getLogger("standupbot.api.auth")

router = APIRouter()


@router.post(
    "/login/google",
    response_model=TokenResponse,
    summary="Google OAuth login",
    description=(
        "Authenticate with a Google OAuth credential. "
        "Creates a new account if this is the user's first login."
    ),
)
async def google_login(request: GoogleAuthRequest, db: DBSession) -> TokenResponse:
    """
    Authenticate or register a manager via Google OAuth.

    THE FULL FLOW:
    1. Frontend calls Google Identity Services → gets a `credential` string.
    2. Frontend POSTs that credential here.
    3. We ask Google "is this credential valid?" (verify_google_token).
    4. If valid, we find/create the user in our database.
    5. We generate our own JWT tokens and return them.
    6. Frontend stores the tokens and uses them for all future API calls.

    NOTE: This endpoint is PUBLIC (no auth required).
    A user can't be authenticated yet — they're trying to log in!
    """
    auth_service = AuthService(db)

    # Step 1: Ask Google to verify the credential
    google_user = await auth_service.verify_google_token(request.credential)
    logger.info(f"Google token verified for: {google_user['email']}")

    # Step 2: Find existing user or create a new one
    user = await auth_service.find_or_create_user(google_user)

    # Step 3: Generate our own JWT tokens
    tokens = await auth_service.generate_tokens(user.id)

    logger.info(f"Login successful for user: {user.email} (id={user.id})")
    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access + refresh token pair.",
)
async def refresh_token(request: RefreshTokenRequest, db: DBSession) -> TokenResponse:
    """
    Refresh an expired access token.

    WHEN IS THIS CALLED?
    - The frontend's Axios interceptor detects a 401 response.
    - It automatically calls this endpoint with the stored refresh token.
    - If successful, it retries the original failed request with the new token.
    - If this also fails, the user is redirected to the login page.

    See: frontend/src/api/client.ts (Axios response interceptor)

    NOTE: This endpoint is PUBLIC (no auth required).
    The refresh token itself IS the authentication — we verify it inside.
    """
    auth_service = AuthService(db)
    tokens = await auth_service.refresh_access_token(request.refresh_token)

    logger.info("Token refreshed successfully")
    return TokenResponse(**tokens)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Invalidate the current session.",
)
async def logout(user_id: CurrentUserId, db: DBSession) -> MessageResponse:
    """
    Logout and invalidate the session.

    IMPORTANT — JWT LOGOUT IS CLIENT-SIDE:
    JWTs are stateless — there's no server-side session to invalidate.
    The "real" logout happens when the frontend deletes the tokens from
    localStorage. This endpoint exists for:
    1. API completeness (clients expect a logout endpoint)
    2. Future: we could blacklist the token in Redis for extra security
    3. Logging/auditing — we know when users deliberately log out
    """
    logger.info(f"User {user_id} logged out")
    return MessageResponse(message="Logged out successfully")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Returns the authenticated user's profile.",
)
async def get_me(user_id: CurrentUserId, db: DBSession) -> UserResponse:
    """
    Get the current authenticated user's profile.

    HOW DOES THIS KNOW WHO THE USER IS?
    - The `user_id: CurrentUserId` parameter is a FastAPI dependency.
    - FastAPI automatically calls `get_current_user_id()` (in dependencies.py).
    - That function extracts the JWT from the Authorization header,
      decodes it, and returns the user_id.
    - By the time this function runs, `user_id` is a verified string UUID.

    WHEN IS THIS CALLED?
    - On page load: the frontend checks if the stored token is still valid.
    - See: frontend/src/context/AuthContext.tsx (useEffect on mount)
    """
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)

    return UserResponse.model_validate(user)
