"""Prometheus metrics endpoint for the node service."""

import psutil
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import Gauge, generate_latest, CONTENT_TYPE_LATEST

from services.node.config.settings import settings
from services.node.monitoring.request_tracker import tracker

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

node_requests_last_30s_gauge = Gauge(
    "trustscale_node_requests_last_30s",
    "Requests completed in the last 30 seconds",
    ["node_id"],
)

node_avg_response_time_gauge = Gauge(
    "trustscale_node_avg_response_time_ms",
    "Average response time in milliseconds over last 30 seconds",
    ["node_id"],
)

node_p95_response_time_gauge = Gauge(
    "trustscale_node_p95_response_time_ms",
    "P95 response time in milliseconds over last 30 seconds",
    ["node_id"],
)


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint."""
    cpu_percent = tracker.cpu_tracker.get_cpu_percent()
    memory_percent = psutil.virtual_memory().percent

    node_cpu_gauge.labels(node_id=settings.node_id).set(cpu_percent)
    node_memory_gauge.labels(node_id=settings.node_id).set(memory_percent)
    node_active_requests_gauge.labels(node_id=settings.node_id).set(
        tracker.active_requests
    )
    node_requests_last_30s_gauge.labels(node_id=settings.node_id).set(
        tracker.get_recent_requests_count(window_seconds=30)
    )
    node_avg_response_time_gauge.labels(node_id=settings.node_id).set(
        tracker.get_average_response_time_ms(window_seconds=30)
    )
    node_p95_response_time_gauge.labels(node_id=settings.node_id).set(
        tracker.get_p95_response_time_ms(window_seconds=30)
    )

    return PlainTextResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )