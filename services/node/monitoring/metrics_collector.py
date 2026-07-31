"""Real local metrics collection for node health reporting."""

import psutil

from services.node.monitoring.request_tracker import tracker
from shared.contracts.health_report import NodeMetrics
from shared.utils.logger import get_logger

logger = get_logger("metrics_collector")


def collect_metrics() -> NodeMetrics:
    """Collect real current node metrics.

    Uses psutil for system metrics and the request tracker
    for application-level metrics.

    Returns:
        Current node metrics with real values.
    """
    cpu_percent = psutil.cpu_percent(interval=None)
    memory = psutil.virtual_memory()

    metrics = NodeMetrics(
        cpu_percent=cpu_percent,
        memory_percent=memory.percent,
        active_requests=tracker.active_requests,
        total_requests_last_5s=tracker.get_recent_requests_count(window_seconds=5),
        avg_response_time_ms=round(
            tracker.get_average_response_time_ms(window_seconds=5), 2
        ),
        uptime_seconds=tracker.uptime_seconds,
    )

    logger.debug(
        "Metrics collected",
        cpu=metrics.cpu_percent,
        memory=metrics.memory_percent,
        active_requests=metrics.active_requests,
        recent_requests=metrics.total_requests_last_5s,
        avg_response_time=metrics.avg_response_time_ms,
    )

    return metrics