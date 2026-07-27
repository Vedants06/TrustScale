"""Redis client for load balancer state storage."""

import redis.asyncio as redis

from services.load_balancer.config.settings import settings
from shared.utils.logger import get_logger

logger = get_logger("redis_client")

_redis_client: redis.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """Get or create Redis client connection.

    Returns:
        Async Redis client instance.
    """
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