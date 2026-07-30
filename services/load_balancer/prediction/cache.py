"""Redis-backed prediction cache for the load balancer."""

import json
import time

from services.load_balancer.storage.redis_client import get_redis_client
from services.load_balancer.storage.schemas.predictions import prediction_key
from shared.contracts.prediction import PredictionResponse
from shared.utils.logger import get_logger

logger = get_logger("prediction_cache")

PREDICTION_TTL_SECONDS = 60


async def cache_predictions(
    predictions: dict[str, PredictionResponse],
) -> None:
    """Store predictions in Redis with TTL.

    Args:
        predictions: Dictionary of node_id to PredictionResponse.
    """
    redis = await get_redis_client()

    for node_id, prediction in predictions.items():
        key = prediction_key(node_id)
        value = prediction.model_dump_json()
        await redis.setex(key, PREDICTION_TTL_SECONDS, value)

    logger.debug(
        "Predictions cached",
        total_nodes=len(predictions),
        ttl_seconds=PREDICTION_TTL_SECONDS,
    )


async def get_cached_prediction(node_id: str) -> PredictionResponse | None:
    """Fetch a cached prediction for a node.

    Args:
        node_id: Node identifier.

    Returns:
        PredictionResponse if cached, None if expired or missing.
    """
    redis = await get_redis_client()
    key = prediction_key(node_id)
    raw = await redis.get(key)

    if raw is None:
        return None

    try:
        data = json.loads(raw)
        return PredictionResponse(**data)
    except Exception as error:
        logger.warning(
            "Failed to deserialize cached prediction",
            node_id=node_id,
            error=str(error),
        )
        return None


async def get_cached_predicted_load(node_id: str) -> float:
    """Get the predicted load value for a node from cache.

    Returns 0.5 as fallback if no cached prediction exists.

    Args:
        node_id: Node identifier.

    Returns:
        Predicted load value between 0.0 and 1.0.
    """
    prediction = await get_cached_prediction(node_id)
    if prediction is None:
        return 0.5

    return prediction.predicted_load