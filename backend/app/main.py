"""
StandupBot Backend — FastAPI Application Factory

Creates and configures the FastAPI application with middleware,
exception handlers, routes, and lifespan management.
"""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.exceptions import register_exception_handlers
from app.api.router import api_router
from app.middleware.logging import RequestLoggingMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("standupbot")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan handler.
    Manages startup and shutdown events for the application.
    """
    # ── Startup ──
    logger.info(f"Starting {settings.APP_NAME} [{settings.APP_ENV}]")

    # TODO: Initialize APScheduler here in Module 4/5
    # from app.tasks.scheduler import start_scheduler
    # start_scheduler()

    logger.info("Application started successfully")

    yield

    # ── Shutdown ──
    logger.info("Shutting down application...")

    # TODO: Shutdown APScheduler here
    # from app.tasks.scheduler import shutdown_scheduler
    # shutdown_scheduler()

    # Close database connections
    from app.database import engine
    await engine.dispose()

    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="Async daily standup collector for remote teams",
        version="0.1.0",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom Middleware ──
    app.add_middleware(RequestLoggingMiddleware)

    # ── Exception Handlers ──
    register_exception_handlers(app)

    # ── Routes ──
    app.include_router(api_router, prefix="/api")

    return app


# Create the application instance
app = create_app()
