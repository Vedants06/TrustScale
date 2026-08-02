"""Trust event history tracking.

Stores and retrieves trust events for each node.
Used for monitoring, debugging, and paper analysis.
"""

import json
import time

from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("trust_history")

MAX_HISTORY_PER_NODE = 100


async def record_trust_event(
    node_id: str,
    event_type: str,
    trust_before: float,
    trust_after: float,
    delta: float,
    discrepancy: float,
    details: str = "",
) -> None:
    """Record a trust event for a node.

    Args:
        node_id: Node identifier.
        event_type: Type of trust event.
        trust_before: Trust score before this event.
        trust_after: Trust score after this event.
        delta: Change in trust score.
        discrepancy: Cross-validation discrepancy value.
        details: Optional additional details.
    """
    redis = await get_redis_client()

    event = {
        "node_id": node_id,
        "event_type": event_type,
        "timestamp": int(time.time()),
        "trust_score_before": round(trust_before, 6),
        "trust_score_after": round(trust_after, 6),
        "delta": round(delta, 6),
        "discrepancy": round(discrepancy, 4),
        "details": details,
    }

    key = f"trust_history:{node_id}"
    await redis.lpush(key, json.dumps(event))
    await redis.ltrim(key, 0, MAX_HISTORY_PER_NODE - 1)


async def get_trust_history(
    node_id: str,
    limit: int = 10,
) -> list[dict]:
    """Get recent trust events for a node.

    Args:
        node_id: Node identifier.
        limit: Maximum number of events to return.

    Returns:
        List of trust events, most recent first.
    """
    redis = await get_redis_client()
    raw_events = await redis.lrange(f"trust_history:{node_id}", 0, limit - 1)

    events = []
    for raw in raw_events:
        try:
            events.append(json.loads(raw))
        except Exception:
            pass

    return events


async def get_all_nodes_trust_summary(node_ids: list[str]) -> dict:
    """Get trust summary for all nodes.

    Args:
        node_ids: List of node identifiers.

    Returns:
        Dictionary mapping node_id to trust summary.
    """
    redis = await get_redis_client()
    summary = {}

    for node_id in node_ids:
        trust_raw = await redis.get(f"trust:{node_id}")
        quarantine_raw = await redis.get(f"quarantine:{node_id}")
        quarantine_count_raw = await redis.get(f"quarantine_count:{node_id}")

        summary[node_id] = {
            "trust_score": float(trust_raw) if trust_raw else 0.5,
            "is_quarantined": quarantine_raw == "true",
            "quarantine_count": int(quarantine_count_raw) if quarantine_count_raw else 0,
        }

    return summary