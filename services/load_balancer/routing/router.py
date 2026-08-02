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

_active_strategy: str = settings.trust_strategy


def get_active_strategy() -> str:
    return _active_strategy


def set_active_strategy(strategy: str) -> None:
    global _active_strategy
    _active_strategy = strategy
    logger.info("Routing strategy updated", strategy=strategy)


async def select_node(strategy: str | None = None) -> NodeTarget | None:
    selected_strategy = strategy or _active_strategy

    if selected_strategy == "trust_aware":
        return await select_trust_aware_node()

    if selected_strategy == "round_robin":
        return await select_round_robin_node()

    logger.warning(
        "Unknown routing strategy, falling back to round_robin",
        strategy=selected_strategy,
    )
    return await select_round_robin_node()