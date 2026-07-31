"""Prometheus metrics endpoint for the node service."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import (
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from services.node.config.settings import settings
from services.node.monitoring.metrics_collector import collect_metrics

router = APIRouter()

node_cpu_gauge = Gauge(
    "trustscale_node_cpu_percent",
    "Node CPU usage percent",
    ["node_id"],
)

node_memory_gauge = Gauge(
    "trustscale_node_memory_percent",
    "Node memory usage percent",
    ["node_id"],
)

node_active_requests_gauge = Gauge(
    "trustscale_node_active_requests",
    "Active requests being processed by the node",
    ["node_id"],
)


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    current_metrics = collect_metrics()

    node_cpu_gauge.labels(node_id=settings.node_id).set(
        current_metrics.cpu_percent
    )
    node_memory_gauge.labels(node_id=settings.node_id).set(
        current_metrics.memory_percent
    )
    node_active_requests_gauge.labels(node_id=settings.node_id).set(
        current_metrics.active_requests
    )

    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )