"""Public key registry for registered nodes."""

import json

from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("key_registry")


async def register_public_key(node_id: str, public_key: str) -> None:
    """Register a node's public key.

    Args:
        node_id: Unique node identifier.
        public_key: PEM-encoded public key string.
    """
    redis = await get_redis_client()
    await redis.set(f"pubkey:{node_id}", public_key)
    logger.info("Public key registered", node_id=node_id)


async def get_public_key(node_id: str) -> str | None:
    """Get a node's registered public key.

    Args:
        node_id: Unique node identifier.

    Returns:
        PEM-encoded public key string, or None if not found.
    """
    redis = await get_redis_client()
    key = await redis.get(f"pubkey:{node_id}")
    return key