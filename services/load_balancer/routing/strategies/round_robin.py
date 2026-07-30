"""Round-robin routing strategy."""

import json
from typing import TypedDict

from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("round_robin")


class NodeTarget(TypedDict):
    """Resolved backend node target."""

    node_id: str
    address: str
    port: int


async def select_round_robin_node() -> NodeTarget | None:
    """Select the next available node using round-robin.

    Uses a Redis counter to rotate across active nodes.

    Returns:
        NodeTarget if a node is available, otherwise None.
    """
    redis = await get_redis_client()

    raw_node_ids = await redis.smembers("nodes:active")
    if not raw_node_ids:
        logger.warning("No active nodes found for round-robin")
        return None

    node_ids = sorted(raw_node_ids)

    valid_nodes: list[NodeTarget] = []

    for node_id in node_ids:
        node_info_raw = await redis.get(f"node:{node_id}")
        if not node_info_raw:
            logger.warning("Skipping node with missing node info", node_id=node_id)
            continue

        try:
            node_info = json.loads(node_info_raw)
            valid_nodes.append(
                NodeTarget(
                    node_id=node_info["node_id"],
                    address=node_info["address"],
                    port=int(node_info["port"]),
                )
            )
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as error:
            logger.warning(
                "Skipping invalid node info",
                node_id=node_id,
                error=str(error),
            )

    if not valid_nodes:
        logger.warning("No valid nodes available for round-robin")
        return None

    counter = await redis.incr("routing:round_robin:index")
    selected_index = (counter - 1) % len(valid_nodes)
    selected_node = valid_nodes[selected_index]

    logger.info(
        "Round-robin selected node",
        node_id=selected_node["node_id"],
        index=selected_index,
        total_nodes=len(valid_nodes),
    )

    return selected_node