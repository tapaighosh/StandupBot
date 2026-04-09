"""
StandupBot — Rate Limiting Middleware

Simple in-memory rate limiter for public endpoints.
For production, replace with Redis-backed rate limiting.
"""

import logging
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("standupbot.ratelimit")

# Default: 60 requests per minute per IP
DEFAULT_RATE_LIMIT = 60
DEFAULT_WINDOW_SECONDS = 60

# Paths that should be rate-limited more aggressively
STRICT_PATHS: dict[str, tuple[int, int]] = {
    "/api/v1/auth/login": (10, 60),  # 10 per minute
    "/api/v1/auth/signup": (5, 60),  # 5 per minute
    "/api/v1/submissions/form": (30, 60),  # 30 per minute
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory token bucket rate limiter.

    WARNING: This is per-instance only. For multi-instance deployments,
    use Redis-backed rate limiting (e.g., slowapi with Redis backend).
    """

    def __init__(self, app: object) -> None:
        super().__init__(app)
        # { ip_address: [(timestamp, count)] }
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        # Determine rate limit for this path
        rate_limit, window = DEFAULT_RATE_LIMIT, DEFAULT_WINDOW_SECONDS
        for strict_path, (limit, win) in STRICT_PATHS.items():
            if path.startswith(strict_path):
                rate_limit, window = limit, win
                break

        # Clean old entries and check rate
        now = time.time()
        key = f"{client_ip}:{path}"
        self._requests[key] = [t for t in self._requests[key] if now - t < window]

        if len(self._requests[key]) >= rate_limit:
            logger.warning(f"Rate limit exceeded for {client_ip} on {path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "code": "RATE_LIMIT_EXCEEDED",
                },
                headers={"Retry-After": str(window)},
            )

        self._requests[key].append(now)
        return await call_next(request)
