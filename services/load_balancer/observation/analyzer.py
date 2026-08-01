"""Analyze observed backend node behavior for trust cross-validation.

Uses the in-memory observation collector to compute real P95 response times
and request counts per node over configurable time windows.
"""

from services.load_balancer.observation.collector import collector
from shared.utils.logger import get_logger

logger = get_logger("observation_analyzer")


def get_observed_p95_response_time(
    node_id: str,
    window_seconds: int = 30,
) -> float | None:
    """Get the observed P95 response time for a node.

    Args:
        node_id: Node identifier.
        window_seconds: Time window to consider.

    Returns:
        P95 response time in milliseconds, or None if insufficient data.
    """
    durations = collector.get_recent_durations_ms(node_id, window_seconds)

    if len(durations) < 3:
        logger.debug(
            "Insufficient observations for P95",
            node_id=node_id,
            observation_count=len(durations),
        )
        return None

    sorted_durations = sorted(durations)
    index = int(len(sorted_durations) * 0.95)
    p95 = sorted_durations[min(index, len(sorted_durations) - 1)]

    logger.debug(
        "Observed P95 computed",
        node_id=node_id,
        p95_ms=round(p95, 2),
        observation_count=len(durations),
        window_seconds=window_seconds,
    )

    return p95


def get_observed_average_response_time(
    node_id: str,
    window_seconds: int = 30,
) -> float | None:
    """Get the observed average response time for a node.

    Args:
        node_id: Node identifier.
        window_seconds: Time window to consider.

    Returns:
        Average response time in milliseconds, or None if insufficient data.
    """
    return collector.get_average_response_time(node_id, window_seconds)


def get_observed_request_count(
    node_id: str,
    window_seconds: int = 30,
) -> int:
    """Get the observed request count for a node.

    Args:
        node_id: Node identifier.
        window_seconds: Time window to consider.

    Returns:
        Number of requests observed in the window.
    """
    return collector.get_request_count(node_id, window_seconds)