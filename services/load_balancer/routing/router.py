"""Routing strategy selector for the load balancer."""

from services.load_balancer.config.settings import settings
from services.load_balancer.routing.strategies.round_robin import (
    NodeTarget,
    select_round_robin_node,
)
from services.load_balancer.routing.strategies.trust_aware import (
    select_trust_aware_node,
)
from shared.utils.logger import get_logger

logger = get_logger("router")


async def select_node(strategy: str | None = None) -> NodeTarget | None:
    """Select a node using the configured routing strategy.

    Args:
        strategy: Optional override for the routing strategy.

    Returns:
        NodeTarget if a node is available, otherwise None.
    """
    selected_strategy = strategy or settings.trust_strategy

    if selected_strategy == "trust_aware":
        return await select_trust_aware_node()

    if selected_strategy == "round_robin":
        return await select_round_robin_node()

    logger.warning(
        "Unknown routing strategy, falling back to round_robin",
        strategy=selected_strategy,
    )
    return await select_round_robin_node()