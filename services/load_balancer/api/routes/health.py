"""Health check and metrics endpoints for the load balancer."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

router = APIRouter()

# Prometheus metrics
lb_requests_total = Counter(
    "trustscale_lb_requests_total",
    "Total number of requests processed by the load balancer",
    ["method", "status_code"],
)

lb_request_duration_ms = Histogram(
    "trustscale_lb_request_duration_ms",
    "Request duration in milliseconds at the load balancer",
    buckets=[5, 10, 25, 50, 100, 150, 200, 300, 500, 1000],
)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "load_balancer"}


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )