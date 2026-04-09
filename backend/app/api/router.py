"""
StandupBot — Main API Router

Aggregates all v1 sub-routers into a single API router.
"""

from fastapi import APIRouter

from app.api.v1 import auth, dashboard, digests, health, submissions, teams

api_router = APIRouter()

# ── V1 Routes ──
api_router.include_router(health.router, prefix="/v1/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/v1/auth", tags=["Authentication"])
api_router.include_router(teams.router, prefix="/v1/teams", tags=["Teams"])
api_router.include_router(submissions.router, prefix="/v1/submissions", tags=["Submissions"])
api_router.include_router(digests.router, prefix="/v1/digests", tags=["Digests"])
api_router.include_router(dashboard.router, prefix="/v1/dashboard", tags=["Dashboard"])
