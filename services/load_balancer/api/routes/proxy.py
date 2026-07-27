"""Proxy route for forwarding requests to backend nodes."""

import json

from fastapi import APIRouter, Request, Response, HTTPException

from services.load_balancer.routing.forwarder import forward_request
from services.load_balancer.storage.redis_client import get_redis_client
from shared.utils.logger import get_logger

logger = get_logger("proxy")

router = APIRouter()


async def get_next_node() -> tuple[str, int] | None:
    """Get the next available node using simple selection.

    Returns:
        Tuple of (address, port) or None if no nodes available.

    Note:
        This is a simple implementation for the walking skeleton.
        Real routing strategies will be implemented in later phases.
    """
    redis = await get_redis_client()

    # Get all active nodes
    nodes = await redis.smembers("nodes:active")
    if not nodes:
        return None

    # For walking skeleton: just pick the first node
    # TODO(Phase 5): Replace with real routing strategy
    node_id = list(nodes)[0]

    # Get node info
    node_info_raw = await redis.get(f"node:{node_id}")
    if not node_info_raw:
        return None

    node_info = json.loads(node_info_raw)
    return node_info["address"], node_info["port"]


@router.api_route("/work", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_work(request: Request):
    """Forward work requests to a backend node.

    This is the main proxy endpoint for the walking skeleton.
    """
    # Get next node
    node = await get_next_node()
    if node is None:
        logger.warning("No nodes available for routing")
        raise HTTPException(status_code=503, detail="No nodes available")

    address, port = node

    # Read request body
    body = await request.body()

    # Forward request
    try:
        status, response_body, response_headers = await forward_request(
            node_address=address,
            node_port=port,
            method=request.method,
            path="/work",
            body=body if body else None,
            headers=dict(request.headers),
        )

        logger.info(
            "Request proxied",
            node_address=address,
            node_port=port,
            status=status,
        )

        return Response(
            content=response_body,
            status_code=status,
            media_type="application/json",
        )

    except Exception as e:
        logger.error("Proxy failed", error=str(e))
        raise HTTPException(status_code=502, detail="Backend node unavailable")