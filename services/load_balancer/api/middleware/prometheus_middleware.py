"""Prometheus metrics middleware for the load balancer."""

from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from services.load_balancer.api.routes.health import (
    lb_request_duration_ms,
    lb_requests_total,
)
from shared.utils.logger import get_logger

logger = get_logger("prometheus_middleware")


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Track request counts and durations for Prometheus."""

    async def dispatch(self, request: Request, call_next) -> Response:
        start = perf_counter()
        response = await call_next(request)
        duration_ms = (perf_counter() - start) * 1000

        lb_requests_total.labels(
            method=request.method,
            status_code=response.status_code,
        ).inc()

        lb_request_duration_ms.observe(duration_ms)

        return response