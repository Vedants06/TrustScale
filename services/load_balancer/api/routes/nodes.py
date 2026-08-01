"""Node registration and heartbeat endpoints."""

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.load_balancer.crypto.keys import register_public_key, get_public_key
from services.load_balancer.crypto.verifier import verify_health_report
from services.load_balancer.storage.redis_client import get_redis_client
from services.load_balancer.prediction.client import update_node_metrics_cache
from shared.contracts.health_report import SignedHealthReport
from shared.utils.logger import get_logger

logger = get_logger("nodes_api")

router = APIRouter(prefix="/nodes", tags=["nodes"])


class NodeRegistration(BaseModel):
    """Node registration request payload."""

    node_id: str
    address: str
    port: int
    public_key: str


@router.post("/register")
async def register_node(registration: NodeRegistration):
    """Register a new node with the load balancer.

    Args:
        registration: Node registration details including public key.

    Returns:
        Registration confirmation.
    """
    # Store public key
    await register_public_key(registration.node_id, registration.public_key)

    # Store node info
    redis = await get_redis_client()
    node_info = {
        "node_id": registration.node_id,
        "address": registration.address,
        "port": registration.port,
    }
    await redis.set(f"node:{registration.node_id}", json.dumps(node_info))

    # Add to active nodes set
    await redis.sadd("nodes:active", registration.node_id)

    logger.info(
        "Node registered",
        node_id=registration.node_id,
        address=registration.address,
        port=registration.port,
    )

    return {"status": "registered", "node_id": registration.node_id}


@router.post("/heartbeat")
async def receive_heartbeat(signed_report: SignedHealthReport):
    """Receive a signed health report from a node."""
    node_id = signed_report.report.node_id

    public_key = await get_public_key(node_id)
    if public_key is None:
        logger.warning("Heartbeat from unregistered node", node_id=node_id)
        raise HTTPException(status_code=404, detail="Node not registered")

    is_valid, error = verify_health_report(signed_report, public_key)

    if not is_valid:
        logger.warning(
            "Heartbeat verification failed",
            node_id=node_id,
            error=error,
        )
        return {"status": "rejected", "node_id": node_id, "reason": error}

    # Feed verified metrics into prediction cache
    update_node_metrics_cache(
        node_id=node_id,
        cpu_percent=signed_report.report.metrics.cpu_percent,
        active_requests=float(signed_report.report.metrics.total_requests_last_5s),
        response_time_ms=signed_report.report.metrics.avg_response_time_ms,
    )

    redis = await get_redis_client()
    await redis.set(
        f"metrics:{node_id}",
        signed_report.report.model_dump_json(),
    )

    logger.info(
        "Heartbeat verified",
        node_id=node_id,
        cpu=signed_report.report.metrics.cpu_percent,
        response_time=signed_report.report.metrics.avg_response_time_ms,
    )

    return {"status": "accepted", "node_id": node_id}

@router.get("")
async def list_nodes():
    """List all registered nodes.

    Returns:
        List of active node IDs.
    """
    redis = await get_redis_client()
    nodes = await redis.smembers("nodes:active")
    return {"nodes": sorted(list(nodes))}