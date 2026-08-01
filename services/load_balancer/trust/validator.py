"""Trust validation through baseline profiling and cross-validation.

The baseline profiler establishes per-node response time profiles.
The validator compares claimed metrics against observed behavior
to detect dishonest nodes.
"""

import json
from collections import defaultdict

from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("trust_validator")

# Default baseline profile if no profiling data exists
# Maps approximate composite load level to expected P95 response time (ms)
DEFAULT_BASELINE_PROFILE = {
    0.0: 5.0,
    0.1: 20.0,
    0.2: 50.0,
    0.3: 100.0,
    0.4: 180.0,
    0.5: 300.0,
    0.6: 500.0,
    0.7: 750.0,
    0.8: 1000.0,
    0.9: 1500.0,
    1.0: 2000.0,
}


async def store_baseline_profile(
    node_id: str,
    profile: dict[float, float],
) -> None:
    """Store a baseline profile for a node in Redis.

    Args:
        node_id: Node identifier.
        profile: Dictionary mapping composite load level to expected P95 response time.
    """
    redis = await get_redis_client()
    key = f"baseline:{node_id}"

    serialized = {str(k): v for k, v in profile.items()}
    await redis.set(key, json.dumps(serialized))

    logger.info(
        "Baseline profile stored",
        node_id=node_id,
        levels=len(profile),
    )


async def load_baseline_profile(node_id: str) -> dict[float, float]:
    """Load a baseline profile for a node from Redis.

    Falls back to default profile if none exists.

    Args:
        node_id: Node identifier.

    Returns:
        Dictionary mapping composite load level to expected P95 response time.
    """
    redis = await get_redis_client()
    key = f"baseline:{node_id}"
    raw = await redis.get(key)

    if raw is None:
        logger.debug(
            "No baseline profile found, using default",
            node_id=node_id,
        )
        return DEFAULT_BASELINE_PROFILE.copy()

    try:
        serialized = json.loads(raw)
        profile = {float(k): float(v) for k, v in serialized.items()}
        return profile
    except Exception as error:
        logger.warning(
            "Failed to parse baseline profile, using default",
            node_id=node_id,
            error=str(error),
        )
        return DEFAULT_BASELINE_PROFILE.copy()


def expected_latency(
    profile: dict[float, float],
    claimed_load: float,
) -> float:
    """Given a node's claimed composite load, return the expected P95 response time.

    Uses linear interpolation between known baseline points.

    Args:
        profile: Baseline profile mapping load levels to expected response times.
        claimed_load: The composite load value the node is claiming.

    Returns:
        Expected P95 response time in milliseconds.
    """
    if not profile:
        return 100.0 + (claimed_load * 1900.0)

    load_levels = sorted(profile.keys())

    claimed_load = max(0.0, min(1.0, claimed_load))

    if claimed_load <= load_levels[0]:
        return profile[load_levels[0]]

    if claimed_load >= load_levels[-1]:
        return profile[load_levels[-1]]

    lower = max(level for level in load_levels if level <= claimed_load)
    upper = min(level for level in load_levels if level >= claimed_load)

    if lower == upper:
        return profile[lower]

    lower_latency = profile[lower]
    upper_latency = profile[upper]
    fraction = (claimed_load - lower) / (upper - lower)

    interpolated = lower_latency + (upper_latency - lower_latency) * fraction
    return round(interpolated, 2)


async def compute_discrepancy(
    node_id: str,
    claimed_load: float,
    observed_p95_ms: float | None,
) -> float:
    """Compare claimed load against observed response time.

    Returns a discrepancy score:
        0.0 = perfect match
        0.15+ = minor discrepancy
        0.30+ = major discrepancy

    Args:
        node_id: Node identifier.
        claimed_load: Composite load the node is claiming.
        observed_p95_ms: Actual observed P95 response time.

    Returns:
        Discrepancy score (0.0 to 1.0+).
    """
    if observed_p95_ms is None or observed_p95_ms <= 0:
        return 0.0

    profile = await load_baseline_profile(node_id)
    expected_p95 = expected_latency(profile, claimed_load)

    if expected_p95 <= 0:
        return 0.0

    discrepancy = abs(observed_p95_ms - expected_p95) / expected_p95

    logger.debug(
        "Discrepancy computed",
        node_id=node_id,
        claimed_load=round(claimed_load, 4),
        expected_p95=round(expected_p95, 2),
        observed_p95=round(observed_p95_ms, 2),
        discrepancy=round(discrepancy, 4),
    )

    return discrepancy