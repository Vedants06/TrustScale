"""Redis client for load balancer state storage."""

import redis.asyncio as redis

from services.load_balancer.config.settings import settings
from services.load_balancer.storage.schemas.predictions import prediction_key
from services.load_balancer.storage.schemas.quarantine import (
    quarantine_key,
    quarantine_since_key,
)
from services.load_balancer.storage.schemas.trust_scores import trust_score_key
from shared.utils.logger import get_logger

logger = get_logger("redis_client")

_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client connection."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        logger.info("Redis client connected", url=settings.redis_url)
    return _redis_client


async def close_redis_client() -> None:
    """Close Redis client connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis client closed")


async def set_prediction(node_id: str, predicted_load: float) -> None:
    """Store cached prediction for a node."""
    redis_client = await get_redis_client()
    await redis_client.set(prediction_key(node_id), predicted_load)


async def get_prediction(node_id: str) -> str | None:
    """Fetch cached prediction for a node."""
    redis_client = await get_redis_client()
    return await redis_client.get(prediction_key(node_id))


async def set_trust_score(node_id: str, score: float) -> None:
    """Store trust score for a node."""
    redis_client = await get_redis_client()
    await redis_client.set(trust_score_key(node_id), score)


async def get_trust_score(node_id: str) -> str | None:
    """Fetch trust score for a node."""
    redis_client = await get_redis_client()
    return await redis_client.get(trust_score_key(node_id))


async def set_quarantine_status(
    node_id: str,
    is_quarantined: bool,
    since_timestamp: int | None = None,
) -> None:
    """Store quarantine state for a node."""
    redis_client = await get_redis_client()
    await redis_client.set(quarantine_key(node_id), str(is_quarantined).lower())

    if since_timestamp is not None:
        await redis_client.set(quarantine_since_key(node_id), since_timestamp)


async def get_quarantine_status(node_id: str) -> str | None:
    """Fetch quarantine flag for a node."""
    redis_client = await get_redis_client()
    return await redis_client.get(quarantine_key(node_id))


async def store_observation_summary(
    node_id: str,
    duration_ms: float,
    timestamp: int,
) -> None:
    """Store last-observed request timing summary for a node."""
    redis_client = await get_redis_client()
    key = f"observation:summary:{node_id}"

    await redis_client.hset(
        key,
        mapping={
            "last_duration_ms": round(duration_ms, 2),
            "last_observed_at": timestamp,
        },
    )
    await redis_client.hincrby(key, "total_requests_observed", 1)