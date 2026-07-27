"""Local metrics collection for node health reporting."""

import time

from shared.contracts.health_report import NodeMetrics
from shared.utils.logger import get_logger

logger = get_logger("metrics_collector")

_start_time = time.time()


def collect_metrics() -> NodeMetrics:
    """Collect current node metrics.

    Returns:
        Current node metrics.

    Note:
        This is a stub implementation for the walking skeleton.
        Real metrics collection will be implemented in Phase 13.
    """
    # STUB: Hardcoded values for walking skeleton
    # TODO(Phase 13): Replace with real psutil metrics
    metrics = NodeMetrics(
        cpu_percent=30.0,
        memory_percent=40.0,
        active_requests=5,
        total_requests_last_5s=10,
        avg_response_time_ms=50.0,
        uptime_seconds=int(time.time() - _start_time),
    )

    logger.debug(
        "Metrics collected",
        cpu=metrics.cpu_percent,
        memory=metrics.memory_percent,
    )

    return metrics