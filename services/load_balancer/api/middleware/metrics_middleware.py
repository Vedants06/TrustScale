"""Basic request metrics middleware for the load balancer."""

from collections import defaultdict
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.utils.logger import get_logger

logger = get_logger("metrics_middleware")

REQUEST_COUNTS: dict[str, int] = defaultdict(int)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Track request counts and durations at the load balancer."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000

        REQUEST_COUNTS[request.url.path] += 1

        logger.debug(
            "Request metric recorded",
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            total_requests=REQUEST_COUNTS[request.url.path],
        )

        return response