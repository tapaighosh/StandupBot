"""
StandupBot — Test Configuration & Shared Fixtures

Provides test database, async client, and factory fixtures.

HOW THE TEST DATABASE WORKS:
1. We use a SEPARATE database called `standupbot_test` (created by scripts/init-db.sql).
2. Before EACH test, we create all tables (fresh schema).
3. After EACH test, we drop all tables (clean slate).
4. The DB session used in tests is the SAME session the API routes use,
   because we override FastAPI's `get_db` dependency.

KEY PATTERN — Session Sharing:
  The test's `db_session` fixture gives us a session.
  When the test client calls an API route, that route calls `get_db()`.
  We override `get_db()` to return the SAME session the test is using.
  This means the test can create data, the API route can read it,
  and we can roll it all back at the end. Clean and isolated.
"""

import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.base import Base

# ──────────────────────────────────────────────────────────────────────
# DATABASE SETUP
# ──────────────────────────────────────────────────────────────────────

# Build test DB URL by replacing only the database name (last segment)
_base_url = settings.DATABASE_URL.rsplit("/", 1)[0]
TEST_DATABASE_URL = f"{_base_url}/standupbot_test"

# Create a dedicated engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=0,
)
test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ──────────────────────────────────────────────────────────────────────
# EVENT LOOP — Required for pytest-asyncio
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ──────────────────────────────────────────────────────────────────────
# DATABASE LIFECYCLE — Create/drop tables per test
# ──────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """
    Create all tables before each test, drop after.
    
    Uses its OWN connection (separate from the test session)
    to avoid "another operation is in progress" errors.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Dispose of all connections to prevent leaks between tests
    await test_engine.dispose()


# ──────────────────────────────────────────────────────────────────────
# DATABASE SESSION — Per-test isolated session
# ──────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated database session for each test.

    After the test, we rollback any uncommitted changes.
    This ensures tests don't leak state to each other.
    """
    async with test_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


# ──────────────────────────────────────────────────────────────────────
# HTTP TEST CLIENT — Simulates API calls without a real server
# ──────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Provide an async HTTP test client.

    This client sends requests directly to our FastAPI app (no network).
    It overrides the database dependency so routes use our test session.
    """

    # Override the DB dependency to use our test session
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────
# TEST DATA FACTORIES — Generate fake data for tests
# ──────────────────────────────────────────────────────────────────────


def make_user_data(**overrides) -> dict:
    """Generate test user data with random unique values."""
    defaults = {
        "email": f"test-{uuid4().hex[:8]}@example.com",
        "name": "Test User",
        "google_id": f"google-{uuid4().hex[:16]}",
    }
    defaults.update(overrides)
    return defaults


def make_team_data(**overrides) -> dict:
    """Generate test team data."""
    defaults = {
        "name": f"Test Team {uuid4().hex[:6]}",
        "timezone": "UTC",
    }
    defaults.update(overrides)
    return defaults


def make_member_data(**overrides) -> dict:
    """Generate test member data."""
    defaults = {
        "email": f"member-{uuid4().hex[:8]}@example.com",
        "name": "Test Member",
    }
    defaults.update(overrides)
    return defaults


# ──────────────────────────────────────────────────────────────────────
# AUTH TEST HELPERS — Creating users + tokens for authenticated tests
# ──────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def create_test_user(db_session: AsyncSession):
    """
    Factory fixture that creates a User directly in the test database.

    Usage:
        user = await create_test_user()
        user = await create_test_user(email="custom@test.com", name="Custom")
    """
    from app.models.user import User

    async def _create(**overrides) -> User:
        data = make_user_data(**overrides)
        user = User(
            email=data["email"],
            name=data["name"],
            google_id=data["google_id"],
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    return _create


def make_auth_headers(user_id: str) -> dict:
    """
    Create an Authorization header with a valid JWT for a given user_id.

    Use this when you need auth headers but don't need the full auth_client fixture.
    """
    from app.utils.security import create_access_token

    token = create_access_token(data={"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, create_test_user):
    """
    Provide an authenticated HTTP client + the user it's authenticated as.

    Usage:
        async def test_something(auth_client):
            client, user = auth_client
            response = await client.get("/api/v1/auth/me")
    """
    user = await create_test_user()
    headers = make_auth_headers(user.id)
    client.headers.update(headers)
    yield client, user


@pytest_asyncio.fixture
async def auth_headers():
    """
    Factory fixture that returns auth headers for a given user.

    Usage:
        headers = await auth_headers(user)
        response = await client.get("/api/v1/...", headers=headers)
    """

    async def _make(user) -> dict:
        return make_auth_headers(user.id)

    return _make
