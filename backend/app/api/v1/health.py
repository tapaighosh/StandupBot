"""
StandupBot — Health Check Endpoints

Provides liveness and readiness probes.
"""

from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text

from app.database import async_session_factory
from app.config import settings
from app.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns OK if the application is running.",
)
async def health_check() -> HealthResponse:
    """Basic health check — confirms the API is alive."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=HealthResponse,
    summary="Readiness probe",
    description="Returns OK if the application can connect to the database.",
)
async def readiness_check() -> HealthResponse:
    """Readiness check — confirms database connectivity."""
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "database_unavailable"

    return HealthResponse(
        status=db_status,
        version="0.1.0",
        environment=settings.APP_ENV,
        timestamp=datetime.now(timezone.utc),
    )
