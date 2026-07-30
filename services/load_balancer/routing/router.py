"""Routing strategy selector for the load balancer."""

from typing import TypedDict

from services.load_balancer.config.settings import settings
from services.load_balancer.routing.strategies.round_robin import select_round_robin_node
from shared.utils.logger import get_logger

logger = get_logger("router")


class NodeTarget(TypedDict):
    """Resolved backend node target."""

    node_id: str
    address: str
    port: int


async def select_node(strategy: str | None = None) -> NodeTarget | None:
    """Select a node using the configured routing strategy.

    Args:
        strategy: Optional override for the routing strategy.

    Returns:
        NodeTarget if a node is available, otherwise None.
    """
    selected_strategy = strategy or settings.trust_strategy

    if selected_strategy == "round_robin":
        return await select_round_robin_node()

    logger.warning(
        "Unknown routing strategy requested, falling back to round_robin",
        strategy=selected_strategy,
    )
    return await select_round_robin_node()