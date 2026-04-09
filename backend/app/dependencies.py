"""
StandupBot Backend — Shared FastAPI Dependencies

Reusable dependencies for database sessions, authentication, and services.

HOW FASTAPI DEPENDENCY INJECTION WORKS:
- You declare a function (like `get_current_user_id` below).
- You annotate it with `Depends()`.
- FastAPI calls it automatically before your route handler runs.
- If it raises an exception, the request is rejected before your handler code executes.

Example: When a route has `user_id: CurrentUserId`, FastAPI:
  1. Reads the Authorization header
  2. Extracts the Bearer token
  3. Decodes the JWT
  4. Returns the user_id string
  All before your route handler even starts.

WHY USE `Annotated[str, Depends(...)]`?
- This is the modern FastAPI pattern (Python 3.9+).
- `CurrentUserId` becomes a reusable type alias.
- Every route that needs auth just says `user_id: CurrentUserId`.
- No boilerplate in every route — DRY (Don't Repeat Yourself).
"""

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.exceptions import AuthenticationError
from app.utils.security import decode_token

# ──────────────────────────────────────────────────────────────────────
# DATABASE SESSION DEPENDENCY
# ──────────────────────────────────────────────────────────────────────

# Every route that needs the database uses this:
#   async def my_route(db: DBSession):
#       result = await db.execute(...)
DBSession = Annotated[AsyncSession, Depends(get_db)]


# ──────────────────────────────────────────────────────────────────────
# AUTHENTICATION DEPENDENCY
# ──────────────────────────────────────────────────────────────────────


async def get_current_user_id(authorization: str | None = Header(default=None)) -> str:
    """
    Extract and validate the current user ID from the Authorization header.

    THE FLOW:
    1. Client sends: `Authorization: Bearer eyJhbGciOi...`
    2. This function extracts the token after "Bearer "
    3. `decode_token()` verifies the JWT signature, expiry, and type
    4. We extract the `sub` claim (the user's UUID)
    5. The route handler receives the user_id as a string

    WHAT CAN GO WRONG:
    - No header → 401 "Authorization header is required"
    - Wrong format (no "Bearer ") → 401 "Invalid authorization header format"
    - Expired token → 401 "Invalid token: Signature has expired"
    - Tampered token → 401 "Invalid token: Signature verification failed"
    - Valid token but no "sub" claim → 401 "Invalid token: missing user ID"

    All of these raise AuthenticationError, which our exception handler
    (in exceptions.py) converts to a JSON response with status 401.
    """
    if not authorization:
        raise AuthenticationError("Authorization header is required")

    if not authorization.startswith("Bearer "):
        raise AuthenticationError("Invalid authorization header format")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Token is required")

    # decode_token() validates signature, expiry, and token type.
    # It will raise AuthenticationError if anything is wrong.
    payload = decode_token(token, expected_type="access")

    # "sub" is the standard JWT claim for "subject" (who this token is for).
    # We set this to the user's UUID when we create the token.
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token: missing user ID")

    return user_id


# Type alias: use this in any route that requires authentication.
# Example: async def my_route(user_id: CurrentUserId):
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
