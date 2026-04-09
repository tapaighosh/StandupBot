"""
StandupBot Backend — Custom Exceptions & Global Error Handlers

All API errors return structured JSON: { "detail": str, "code": str }
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# =============================================================================
# Custom Exception Hierarchy
# =============================================================================


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, detail: str, code: str = "APP_ERROR", status_code: int = 500) -> None:
        self.detail = detail
        self.code = code
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, detail: str = "Resource not found", resource: str = "") -> None:
        resource_msg = f"{resource} not found" if resource else detail
        super().__init__(detail=resource_msg, code="NOT_FOUND", status_code=404)


class AuthenticationError(AppException):
    """Authentication failed."""

    def __init__(self, detail: str = "Authentication failed") -> None:
        super().__init__(detail=detail, code="AUTHENTICATION_ERROR", status_code=401)


class AuthorizationError(AppException):
    """User not authorized for this action."""

    def __init__(self, detail: str = "You do not have permission to perform this action") -> None:
        super().__init__(detail=detail, code="AUTHORIZATION_ERROR", status_code=403)


class ValidationError(AppException):
    """Input validation error."""

    def __init__(self, detail: str = "Validation error") -> None:
        super().__init__(detail=detail, code="VALIDATION_ERROR", status_code=422)


class ConflictError(AppException):
    """Resource conflict (e.g., duplicate)."""

    def __init__(self, detail: str = "Resource already exists") -> None:
        super().__init__(detail=detail, code="CONFLICT", status_code=409)


class RateLimitError(AppException):
    """Rate limit exceeded."""

    def __init__(self, detail: str = "Too many requests. Please try again later.") -> None:
        super().__init__(detail=detail, code="RATE_LIMIT_EXCEEDED", status_code=429)


class ExternalServiceError(AppException):
    """External service (LLM, email, Slack, Stripe) failure."""

    def __init__(self, detail: str = "External service unavailable", service: str = "") -> None:
        service_msg = f"{service} service error: {detail}" if service else detail
        super().__init__(detail=service_msg, code="EXTERNAL_SERVICE_ERROR", status_code=502)


class TokenExpiredError(AppException):
    """Standup token has expired."""

    def __init__(self, detail: str = "This standup link has expired") -> None:
        super().__init__(detail=detail, code="TOKEN_EXPIRED", status_code=410)


class TokenUsedError(AppException):
    """Standup token has already been used."""

    def __init__(self, detail: str = "You have already submitted your standup") -> None:
        super().__init__(detail=detail, code="TOKEN_ALREADY_USED", status_code=409)


class PlanLimitError(AppException):
    """Plan limit exceeded."""

    def __init__(self, detail: str = "Plan limit reached. Please upgrade.") -> None:
        super().__init__(detail=detail, code="PLAN_LIMIT_EXCEEDED", status_code=403)


class SubmissionWindowClosedError(AppException):
    """Submission window is closed."""

    def __init__(self, detail: str = "The submission window for today has closed") -> None:
        super().__init__(detail=detail, code="SUBMISSION_WINDOW_CLOSED", status_code=403)


# =============================================================================
# Global Exception Handlers
# =============================================================================


def register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "code": exc.code,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log the full exception in non-production environments
        import logging

        logger = logging.getLogger("standupbot")
        logger.exception(f"Unhandled exception on {request.method} {request.url.path}")

        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred. Please try again later.",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )
