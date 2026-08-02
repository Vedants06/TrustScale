"""Trust-aware routing strategy combining real ML predictions and trust scores.

This is the core routing contribution of TrustScale.

Routing Score = (predicted_load × 0.6) + ((1 - trust_score) × 0.4)
Lowest score wins.

Nodes below the quarantine threshold are excluded entirely.
"""

import json

from services.load_balancer.prediction.cache import get_cached_predicted_load
from services.load_balancer.routing.strategies.round_robin import NodeTarget
from services.load_balancer.storage.redis_client import get_redis_client
from services.load_balancer.trust.quarantine import is_node_quarantined
from shared.utils.logger import get_logger

logger = get_logger("trust_aware")

PREDICTED_LOAD_WEIGHT = 0.6
TRUST_SCORE_WEIGHT = 0.4
DEFAULT_TRUST_SCORE = 0.5


async def select_trust_aware_node() -> NodeTarget | None:
    """Select the best node using combined prediction and trust scoring.

    Routing Score = (predicted_load × 0.6) + ((1 - trust_score) × 0.4)
    Lowest score wins.

    Quarantined nodes are completely excluded.
    When scores are tied, uses round-robin as tiebreaker.

    Returns:
        NodeTarget for the best available node, or None if no nodes available.
    """
    redis = await get_redis_client()

    raw_node_ids = await redis.smembers("nodes:active")
    if not raw_node_ids:
        logger.warning("No active nodes found for trust-aware routing")
        return None

    node_ids = sorted(raw_node_ids)
    scored_nodes: list[tuple[float, NodeTarget]] = []

    for node_id in node_ids:
        # Check quarantine first — skip quarantined nodes entirely
        if await is_node_quarantined(node_id):
            logger.debug("Skipping quarantined node", node_id=node_id)
            continue

        node_info_raw = await redis.get(f"node:{node_id}")
        if not node_info_raw:
            logger.warning("Skipping node with missing info", node_id=node_id)
            continue

        try:
            node_info = json.loads(node_info_raw)
        except Exception:
            logger.warning("Skipping node with invalid info", node_id=node_id)
            continue

        # Get real predicted load from ML service cache
        predicted_load = await get_cached_predicted_load(node_id)

        # Get real trust score from Redis
        trust_raw = await redis.get(f"trust:{node_id}")
        trust_score = float(trust_raw) if trust_raw else DEFAULT_TRUST_SCORE
        trust_score = max(0.0, min(1.0, trust_score))

        # Compute combined routing score
        combined_score = (
            predicted_load * PREDICTED_LOAD_WEIGHT
            + (1.0 - trust_score) * TRUST_SCORE_WEIGHT
        )

        logger.debug(
            "Node scoring",
            node_id=node_id,
            predicted_load=round(predicted_load, 3),
            trust_score=round(trust_score, 3),
            combined_score=round(combined_score, 3),
        )

        scored_nodes.append((
            combined_score,
            NodeTarget(
                node_id=node_info["node_id"],
                address=node_info["address"],
                port=int(node_info["port"]),
            )
        ))

    if not scored_nodes:
        logger.warning("No eligible nodes for trust-aware routing")
        return None

    # Find minimum score
    min_score = min(score for score, _ in scored_nodes)

    # Collect all tied nodes
    tied_nodes = [
        node for score, node in scored_nodes
        if abs(score - min_score) < 1e-9
    ]

    # Use round-robin as tiebreaker
    if len(tied_nodes) == 1:
        selected = tied_nodes[0]
    else:
        counter = await redis.incr("routing:trust_aware:tiebreak_index")
        selected_index = (counter - 1) % len(tied_nodes)
        selected = tied_nodes[selected_index]

    logger.info(
        "Trust-aware selected node",
        node_id=selected["node_id"],
        best_score=round(min_score, 3),
        eligible_nodes=len(scored_nodes),
        tied_nodes=len(tied_nodes),
    )

    return selected