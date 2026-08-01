"""Composite load calculation shared across services."""


CPU_WEIGHT = 0.2
ACTIVE_REQUESTS_WEIGHT = 0.3
RESPONSE_TIME_WEIGHT = 0.5

MAX_ACTIVE_REQUESTS = 50.0
MAX_RESPONSE_TIME_MS = 2000.0


def compute_composite_load(
    cpu_percent: float,
    active_requests: float,
    response_time_ms: float,
) -> float:
    """Compute composite load score from raw metrics.

    Formula (response-time primary):
        load = 0.2 × normalized_cpu +
               0.3 × normalized_active_requests +
               0.5 × normalized_response_time

    Args:
        cpu_percent: CPU usage 0-100.
        active_requests: Number of recent requests.
        response_time_ms: Average response time in milliseconds.

    Returns:
        Composite load score between 0.0 and 1.0.
    """
    normalized_cpu = cpu_percent / 100.0
    normalized_requests = min(active_requests / MAX_ACTIVE_REQUESTS, 1.0)
    normalized_response_time = min(response_time_ms / MAX_RESPONSE_TIME_MS, 1.0)

    load = (
        CPU_WEIGHT * normalized_cpu
        + ACTIVE_REQUESTS_WEIGHT * normalized_requests
        + RESPONSE_TIME_WEIGHT * normalized_response_time
    )

    return max(0.0, min(1.0, load))