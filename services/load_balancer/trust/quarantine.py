"""Quarantine management for dishonest nodes.

A node is quarantined when its trust score drops below QUARANTINE_THRESHOLD.
Quarantined nodes are excluded from all routing decisions.
Recovery happens after a minimum duration of honest behavior.
"""

import time

from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("quarantine")

QUARANTINE_THRESHOLD = 0.30
QUARANTINE_BASE_DURATION_SECONDS = 60

# Escalating quarantine durations based on repeat offenses
QUARANTINE_DURATIONS = {
    1: 60,
    2: 300,
    3: 1800,
    4: 86400,
}


def get_quarantine_duration(quarantine_count: int) -> int:
    """Get quarantine duration based on repeat offense count.

    Args:
        quarantine_count: How many times this node has been quarantined.

    Returns:
        Quarantine duration in seconds.
    """
    if quarantine_count in QUARANTINE_DURATIONS:
        return QUARANTINE_DURATIONS[quarantine_count]

    if quarantine_count >= 5:
        return -1  # Permanent

    return QUARANTINE_BASE_DURATION_SECONDS


async def is_node_quarantined(node_id: str) -> bool:
    """Check if a node is currently quarantined.

    Args:
        node_id: Node identifier.

    Returns:
        True if node is quarantined and quarantine has not expired.
    """
    redis = await get_redis_client()

    quarantine_raw = await redis.get(f"quarantine:{node_id}")
    if quarantine_raw != "true":
        return False

    quarantine_count_raw = await redis.get(f"quarantine_count:{node_id}")
    quarantine_count = int(quarantine_count_raw) if quarantine_count_raw else 1

    # Check if permanent
    duration = get_quarantine_duration(quarantine_count)
    if duration == -1:
        logger.debug("Node is permanently quarantined", node_id=node_id)
        return True

    # Check if quarantine has expired
    since_raw = await redis.get(f"quarantine_since:{node_id}")
    if since_raw is None:
        return True

    quarantine_since = float(since_raw)
    elapsed = time.time() - quarantine_since

    if elapsed >= duration:
        logger.info(
            "Quarantine expired, allowing probe request",
            node_id=node_id,
            duration_seconds=duration,
            elapsed_seconds=round(elapsed, 1),
        )
        return False

    logger.debug(
        "Node is quarantined",
        node_id=node_id,
        remaining_seconds=round(duration - elapsed, 1),
    )
    return True


async def quarantine_node(node_id: str, quarantine_count: int) -> None:
    """Put a node into quarantine.

    Args:
        node_id: Node identifier.
        quarantine_count: Current quarantine count for this node.
    """
    redis = await get_redis_client()
    duration = get_quarantine_duration(quarantine_count)

    await redis.set(f"quarantine:{node_id}", "true")
    await redis.set(f"quarantine_since:{node_id}", time.time())
    await redis.set(f"quarantine_count:{node_id}", quarantine_count)

    duration_str = "permanent" if duration == -1 else f"{duration}s"

    logger.warning(
        "Node quarantined",
        node_id=node_id,
        quarantine_count=quarantine_count,
        duration=duration_str,
    )


async def restore_node(node_id: str) -> None:
    """Remove a node from quarantine.

    Args:
        node_id: Node identifier.
    """
    redis = await get_redis_client()

    await redis.set(f"quarantine:{node_id}", "false")
    await redis.delete(f"quarantine_since:{node_id}")

    logger.info("Node restored from quarantine", node_id=node_id)


async def get_quarantine_status(node_id: str) -> dict:
    """Get full quarantine status for a node.

    Args:
        node_id: Node identifier.

    Returns:
        Dictionary with quarantine details.
    """
    redis = await get_redis_client()

    quarantine_raw = await redis.get(f"quarantine:{node_id}")
    is_quarantined = quarantine_raw == "true"

    quarantine_count_raw = await redis.get(f"quarantine_count:{node_id}")
    quarantine_count = int(quarantine_count_raw) if quarantine_count_raw else 0

    since_raw = await redis.get(f"quarantine_since:{node_id}")
    quarantine_since = float(since_raw) if since_raw else None

    remaining_seconds = None
    if is_quarantined and quarantine_since:
        duration = get_quarantine_duration(quarantine_count)
        if duration == -1:
            remaining_seconds = -1
        else:
            remaining_seconds = max(
                0,
                duration - (time.time() - quarantine_since)
            )

    return {
        "is_quarantined": is_quarantined,
        "quarantine_count": quarantine_count,
        "quarantine_since": quarantine_since,
        "remaining_seconds": remaining_seconds,
    }