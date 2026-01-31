"""
FastAPI Middleware

Provides cross-cutting concerns:
- Request ID tracking for distributed tracing
- Request timing metrics
- Slow request detection
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.infrastructure.logging_config import set_request_id, reset_request_id

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Unified observability middleware combining request ID tracking and timing.

    - Generates unique request ID for each request
    - Sets ID in context for logging (properly reset via token)
    - Adds X-Request-ID header to response
    - Logs request completion with timing
    - Logs slow requests as warnings
    """

    EXCLUDED_PATHS = ("/health", "/static", "/images", "/docs", "/openapi")

    def __init__(self, app, slow_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate short request ID (8 chars is enough for correlation)
        request_id = str(uuid.uuid4())[:8]

        # Set in context for logging (returns token for proper reset)
        token = set_request_id(request_id)
        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)
        except Exception as e:
            # Log error with timing
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "%s %s failed after %.1fms: %s",
                request.method,
                request.url.path,
                duration_ms,
                str(e),
            )
            raise
        finally:
            # Always reset context to prevent leakage between requests
            reset_request_id(token)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Log request completion (skip health checks and static files)
        path = request.url.path
        if not path.startswith(self.EXCLUDED_PATHS):
            if duration_ms > self.slow_threshold_ms:
                logger.warning(
                    "SLOW REQUEST: %s %s took %.1fms",
                    request.method,
                    path,
                    duration_ms,
                )
            else:
                logger.info(
                    "%s %s completed in %.1fms (status=%d)",
                    request.method,
                    path,
                    duration_ms,
                    response.status_code,
                )

        return response
