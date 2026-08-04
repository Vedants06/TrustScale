"""Trust validation through composite load cross-validation.

Compares the node's claimed composite load against
the load balancer's observed composite load.
"""

from services.load_balancer.observation.analyzer import (
    get_observed_p95_response_time,
    get_observed_average_response_time,
    get_observed_request_count,
)
from shared.utils.composite_load import compute_composite_load
from shared.contracts.health_report import HealthReport
from shared.utils.logger import get_logger

logger = get_logger("trust_validator")


async def cross_validate_heartbeat(
    node_id: str,
    report: HealthReport,
) -> dict:
    """Cross-validate using composite load comparison."""

    claimed_response_time = report.metrics.avg_response_time_ms
    claimed_requests_5s = report.metrics.total_requests_last_5s

    claimed_load = compute_composite_load(
        cpu_percent=report.metrics.cpu_percent,
        active_requests=float(report.metrics.total_requests_last_5s),
        response_time_ms=report.metrics.avg_response_time_ms,
    )

    observed_avg = get_observed_average_response_time(node_id, window_seconds=30)
    observed_count = get_observed_request_count(node_id, window_seconds=30)
    observed_p95 = get_observed_p95_response_time(node_id, window_seconds=30)

    has_sufficient_data = observed_avg is not None and observed_count >= 3

    if not has_sufficient_data:
        logger.debug(
            "Insufficient observation data",
            node_id=node_id,
            observed_count=observed_count,
        )
        return {
            "claimed_load": round(claimed_load, 4),
            "claimed_response_time": round(claimed_response_time, 2),
            "claimed_requests_5s": claimed_requests_5s,
            "observed_load": None,
            "observed_avg": None,
            "observed_p95": None,
            "observed_count": observed_count,
            "discrepancy": 0.0,
            "has_sufficient_data": False,
        }

    observed_load = compute_composite_load(
        cpu_percent=report.metrics.cpu_percent,
        active_requests=float(observed_count),
        response_time_ms=observed_avg,
    )

    if observed_load < 0.01 and claimed_load < 0.01:
        discrepancy = 0.0
    else:
        max_load = max(observed_load, claimed_load, 0.01)
        discrepancy = abs(observed_load - claimed_load) / max_load
        discrepancy = min(discrepancy, 2.0)

    logger.info(
        "Cross-validation result",
        node_id=node_id,
        claimed_load=round(claimed_load, 4),
        observed_load=round(observed_load, 4),
        claimed_rt=round(claimed_response_time, 2),
        observed_avg=round(observed_avg, 2),
        observed_count=observed_count,
        discrepancy=round(discrepancy, 4),
    )

    return {
        "claimed_load": round(claimed_load, 4),
        "claimed_response_time": round(claimed_response_time, 2),
        "claimed_requests_5s": claimed_requests_5s,
        "observed_load": round(observed_load, 4),
        "observed_avg": round(observed_avg, 2),
        "observed_p95": round(observed_p95, 2) if observed_p95 else None,
        "observed_count": observed_count,
        "discrepancy": round(discrepancy, 4),
        "has_sufficient_data": True,
    }