"""
StandupBot — Request/Response Logging Middleware

Logs every incoming request and outgoing response with timing information.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("standupbot.requests")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs request/response details and injects a request ID."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id

        # Log incoming request
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"| client={request.client.host if request.client else 'unknown'}"
        )

        # Time the request
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] ✕ {request.method} {request.url.path} "
                f"| {duration_ms:.1f}ms | error={exc.__class__.__name__}"
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response
        log_method = logger.info if response.status_code < 400 else logger.warning
        log_method(
            f"[{request_id}] ← {request.method} {request.url.path} "
            f"| {response.status_code} | {duration_ms:.1f}ms"
        )

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response
