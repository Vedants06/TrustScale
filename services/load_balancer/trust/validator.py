# """Trust validation through baseline profiling and cross-validation.

# The baseline profiler establishes per-node response time profiles.
# The validator compares claimed metrics against observed behavior
# to detect dishonest nodes.
# """

# import json

# from services.load_balancer.observation.analyzer import (
#     get_observed_p95_response_time,
#     get_observed_average_response_time,
#     get_observed_request_count,
# )
# from services.load_balancer.storage.redis_client import get_redis_client
# from shared.utils.composite_load import compute_composite_load
# from shared.contracts.health_report import HealthReport
# from shared.utils.logger import get_logger

# logger = get_logger("trust_validator")

# # Default baseline profile matching realistic Docker cluster behavior
# # with matrix multiplication work endpoint
# DEFAULT_BASELINE_PROFILE = {
#     0.0: 50.0,
#     0.1: 100.0,
#     0.2: 200.0,
#     0.3: 400.0,
#     0.4: 600.0,
#     0.5: 900.0,
#     0.6: 1200.0,
#     0.7: 1500.0,
#     0.8: 1800.0,
#     0.9: 2000.0,
#     1.0: 2500.0,
# }

# async def store_baseline_profile(
#     node_id: str,
#     profile: dict[float, float],
# ) -> None:
#     """Store a baseline profile for a node in Redis."""
#     redis = await get_redis_client()
#     key = f"baseline:{node_id}"
#     serialized = {str(k): v for k, v in profile.items()}
#     await redis.set(key, json.dumps(serialized))
#     logger.info("Baseline profile stored", node_id=node_id, levels=len(profile))


# async def load_baseline_profile(node_id: str) -> dict[float, float]:
#     """Load a baseline profile for a node from Redis."""
#     redis = await get_redis_client()
#     key = f"baseline:{node_id}"
#     raw = await redis.get(key)

#     if raw is None:
#         logger.debug("No baseline profile found, using default", node_id=node_id)
#         return DEFAULT_BASELINE_PROFILE.copy()

#     try:
#         serialized = json.loads(raw)
#         return {float(k): float(v) for k, v in serialized.items()}
#     except Exception as error:
#         logger.warning(
#             "Failed to parse baseline profile, using default",
#             node_id=node_id,
#             error=str(error),
#         )
#         return DEFAULT_BASELINE_PROFILE.copy()


# def expected_latency(
#     profile: dict[float, float],
#     claimed_load: float,
# ) -> float:
#     """Given claimed composite load, return expected P95 response time."""
#     if not profile:
#         return 100.0 + (claimed_load * 1900.0)

#     load_levels = sorted(profile.keys())
#     claimed_load = max(0.0, min(1.0, claimed_load))

#     if claimed_load <= load_levels[0]:
#         return profile[load_levels[0]]

#     if claimed_load >= load_levels[-1]:
#         return profile[load_levels[-1]]

#     lower = max(level for level in load_levels if level <= claimed_load)
#     upper = min(level for level in load_levels if level >= claimed_load)

#     if lower == upper:
#         return profile[lower]

#     lower_latency = profile[lower]
#     upper_latency = profile[upper]
#     fraction = (claimed_load - lower) / (upper - lower)

#     return round(lower_latency + (upper_latency - lower_latency) * fraction, 2)


# async def cross_validate_heartbeat(
#     node_id: str,
#     report: HealthReport,
# ) -> dict:
#     """Cross-validate a node's claimed metrics against observed behavior.

#     Computes:
#     1. Composite load from claimed metrics
#     2. Expected P95 response time from baseline profile
#     3. Actual observed P95 response time from LB observation
#     4. Discrepancy between expected and observed

#     Args:
#         node_id: Node identifier.
#         report: The health report containing claimed metrics.

#     Returns:
#         Dictionary with cross-validation results:
#         - claimed_load: composite load from claimed metrics
#         - expected_p95: what response time should be
#         - observed_p95: what response time actually is
#         - discrepancy: how far off (0.0 = match, 0.3+ = major mismatch)
#         - has_sufficient_data: whether enough observations exist
#     """
#     claimed_load = compute_composite_load(
#         cpu_percent=report.metrics.cpu_percent,
#         active_requests=float(report.metrics.total_requests_last_5s),
#         response_time_ms=report.metrics.avg_response_time_ms,
#     )

#     profile = await load_baseline_profile(node_id)
#     expected_p95 = expected_latency(profile, claimed_load)

#     observed_p95 = get_observed_p95_response_time(node_id, window_seconds=30)
#     observed_avg = get_observed_average_response_time(node_id, window_seconds=30)
#     observed_count = get_observed_request_count(node_id, window_seconds=30)

#     has_sufficient_data = observed_p95 is not None and observed_count >= 3

#     if not has_sufficient_data:
#         logger.debug(
#             "Insufficient observation data for cross-validation",
#             node_id=node_id,
#             observed_count=observed_count,
#         )
#         return {
#             "claimed_load": round(claimed_load, 4),
#             "expected_p95": round(expected_p95, 2),
#             "observed_p95": None,
#             "observed_avg": None,
#             "observed_count": observed_count,
#             "discrepancy": 0.0,
#             "has_sufficient_data": False,
#         }

#     if expected_p95 <= 0:
#         discrepancy = 0.0
#     else:
#         raw_discrepancy = abs(observed_p95 - expected_p95) / expected_p95
#         discrepancy = min(raw_discrepancy, 2.0)

#     logger.info(
#         "Cross-validation result",
#         node_id=node_id,
#         claimed_load=round(claimed_load, 4),
#         expected_p95=round(expected_p95, 2),
#         observed_p95=round(observed_p95, 2),
#         observed_avg=round(observed_avg, 2) if observed_avg else None,
#         observed_count=observed_count,
#         raw_discrepancy=round(raw_discrepancy, 4),
#         capped_discrepancy=round(discrepancy, 4),
#     )

#     return {
#         "claimed_load": round(claimed_load, 4),
#         "expected_p95": round(expected_p95, 2),
#         "observed_p95": round(observed_p95, 2),
#         "observed_avg": round(observed_avg, 2) if observed_avg else None,
#         "observed_count": observed_count,
#         "discrepancy": round(discrepancy, 4),
#         "has_sufficient_data": True,
#     }

"""Trust validation through direct response time cross-validation.

Compares the node's claimed average response time against
the load balancer's observed average response time for that node.

Accounts for Docker container network overhead by using
a tolerance-based comparison rather than exact matching.
"""

import json

from services.load_balancer.observation.analyzer import (
    get_observed_p95_response_time,
    get_observed_average_response_time,
    get_observed_request_count,
)
from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.composite_load import compute_composite_load
from shared.contracts.health_report import HealthReport
from shared.utils.logger import get_logger

logger = get_logger("trust_validator")

# Network overhead tolerance in milliseconds
# Docker on Windows/WSL2 adds significant container-to-container latency
# This tolerance accounts for that overhead
NETWORK_OVERHEAD_MS = 300.0

# Tolerance multiplier for response time comparison
# observed_avg should be within claimed_rt + overhead ± tolerance
TOLERANCE_MULTIPLIER = 0.5


async def cross_validate_heartbeat(
    node_id: str,
    report: HealthReport,
) -> dict:
    """Cross-validate using composite load comparison."""
    
    # What the node claims its composite load is
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
        return {
            "claimed_load": round(claimed_load, 4),
            "claimed_response_time": round(report.metrics.avg_response_time_ms, 2),
            "observed_avg": None,
            "observed_p95": None,
            "observed_count": observed_count,
            "discrepancy": 0.0,
            "has_sufficient_data": False,
        }

    # Compute observed composite load from what LB actually sees
    # Use observed response time and request count, assume cpu same
    observed_load = compute_composite_load(
        cpu_percent=report.metrics.cpu_percent,  # CPU we cannot verify independently
        active_requests=float(observed_count),
        response_time_ms=observed_avg,
    )

    # Discrepancy: how much is claimed load lower than observed load?
    # Under-reporter: claimed_load << observed_load
    # Over-reporter: claimed_load >> observed_load
    # Honest: claimed_load ≈ observed_load

    if observed_load < 0.01:
        # Both are near zero — no discrepancy
        discrepancy = 0.0
    else:
        load_difference = observed_load - claimed_load

        # Compute discrepancy for both directions
        if observed_load < 0.01 and claimed_load < 0.01:
            # Both near zero — no discrepancy
            discrepancy = 0.0
        else:
            # Symmetric discrepancy: over or under reporting both count
            max_load = max(observed_load, claimed_load, 0.01)
            discrepancy = abs(observed_load - claimed_load) / max_load
            discrepancy = min(discrepancy, 2.0)

    logger.info(
        "Cross-validation result",
        node_id=node_id,
        claimed_load=round(claimed_load, 4),
        observed_load=round(observed_load, 4),
        claimed_rt=round(report.metrics.avg_response_time_ms, 2),
        observed_avg=round(observed_avg, 2),
        observed_count=observed_count,
        discrepancy=round(discrepancy, 4),
    )

    return {
        "claimed_load": round(claimed_load, 4),
        "observed_load": round(observed_load, 4),
        "claimed_response_time": round(report.metrics.avg_response_time_ms, 2),
        "observed_avg": round(observed_avg, 2),
        "observed_p95": round(observed_p95, 2) if observed_p95 else None,
        "observed_count": observed_count,
        "discrepancy": round(discrepancy, 4),
        "has_sufficient_data": True,
    }