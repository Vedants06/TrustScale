"""Node registration and heartbeat endpoints."""

import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.load_balancer.crypto.keys import register_public_key, get_public_key
from services.load_balancer.crypto.verifier import verify_health_report
from services.load_balancer.prediction.client import update_node_metrics_cache
from services.load_balancer.storage.redis_client import get_redis_client
from services.load_balancer.trust.history import get_trust_history, record_trust_event
from services.load_balancer.trust.quarantine import (
    get_quarantine_status,
    quarantine_node,
    restore_node,
)
from services.load_balancer.trust.scorer import update_trust_score
from services.load_balancer.trust.validator import cross_validate_heartbeat
from services.load_balancer.api.routes.trust_metrics import (
    discrepancy_gauge,
    quarantine_count_gauge,
    quarantine_status_gauge,
    trust_score_gauge,
)
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
    """Register a new node with the load balancer."""
    await register_public_key(registration.node_id, registration.public_key)

    redis = await get_redis_client()
    node_info = {
        "node_id": registration.node_id,
        "address": registration.address,
        "port": registration.port,
    }
    await redis.set(f"node:{registration.node_id}", json.dumps(node_info))
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
    """Receive, validate, cross-validate, score, and quarantine check."""
    node_id = signed_report.report.node_id

    # Step 1: Get public key
    public_key = await get_public_key(node_id)
    if public_key is None:
        logger.warning("Heartbeat from unregistered node", node_id=node_id)
        raise HTTPException(status_code=404, detail="Node not registered")

    # Step 2: Verify JWT signature
    is_valid, error = verify_health_report(signed_report, public_key)

    if not is_valid:
        logger.warning(
            "Heartbeat verification failed",
            node_id=node_id,
            error=error,
        )
        trust_event = await update_trust_score(
            node_id=node_id,
            discrepancy=1.0,
            signature_valid=(error != "invalid_signature"),
            timestamp_fresh=(error != "timestamp_stale"),
            has_sufficient_data=False,
        )

        # Update Prometheus metrics
        trust_score_gauge.labels(node_id=node_id).set(
            trust_event["trust_score_after"]
        )
        quarantine_status_gauge.labels(node_id=node_id).set(
            1 if trust_event["is_quarantined"] else 0
        )
        quarantine_count_gauge.labels(node_id=node_id).set(
            trust_event["quarantine_count"]
        )

        return {"status": "rejected", "node_id": node_id, "reason": error}

    # Step 3: Feed verified metrics into prediction cache
    update_node_metrics_cache(
        node_id=node_id,
        cpu_percent=signed_report.report.metrics.cpu_percent,
        active_requests=float(signed_report.report.metrics.total_requests_last_5s),
        response_time_ms=signed_report.report.metrics.avg_response_time_ms,
    )

    # Step 4: Cross-validate claimed vs observed
    cv_result = await cross_validate_heartbeat(node_id, signed_report.report)

    # Step 5: Update trust score
    trust_event = await update_trust_score(
        node_id=node_id,
        discrepancy=cv_result["discrepancy"],
        signature_valid=True,
        timestamp_fresh=True,
        has_sufficient_data=cv_result["has_sufficient_data"],
    )

    # Step 6: Handle quarantine
    if trust_event["is_quarantined"]:
        await quarantine_node(
            node_id=node_id,
            quarantine_count=trust_event["quarantine_count"],
        )
    elif trust_event["trust_score_after"] > 0.35:
        await restore_node(node_id)

    # Step 7: Update Prometheus metrics
    trust_score_gauge.labels(node_id=node_id).set(
        trust_event["trust_score_after"]
    )
    quarantine_status_gauge.labels(node_id=node_id).set(
        1 if trust_event["is_quarantined"] else 0
    )
    quarantine_count_gauge.labels(node_id=node_id).set(
        trust_event["quarantine_count"]
    )
    discrepancy_gauge.labels(node_id=node_id).set(
        cv_result["discrepancy"]
    )

    # Step 8: Store latest metrics in Redis
    redis = await get_redis_client()
    await redis.set(
        f"metrics:{node_id}",
        signed_report.report.model_dump_json(),
    )
    await redis.set(
        f"cv:{node_id}",
        json.dumps(cv_result),
    )

    logger.info(
        "Heartbeat processed",
        node_id=node_id,
        trust_score=trust_event["trust_score_after"],
        event_type=trust_event["event_type"],
        discrepancy=cv_result["discrepancy"],
        quarantined=trust_event["is_quarantined"],
    )

    return {
        "status": "accepted",
        "node_id": node_id,
        "trust_score": trust_event["trust_score_after"],
        "discrepancy": cv_result["discrepancy"],
        "is_quarantined": trust_event["is_quarantined"],
    }


@router.get("")
async def list_nodes():
    """List all registered nodes."""
    redis = await get_redis_client()
    nodes = await redis.smembers("nodes:active")
    return {"nodes": sorted(list(nodes))}


@router.get("/{node_id}/trust")
async def get_node_trust(node_id: str):
    """Get full trust status for a node."""
    redis = await get_redis_client()

    trust_raw = await redis.get(f"trust:{node_id}")
    trust_score = float(trust_raw) if trust_raw else None

    bootstrap_raw = await redis.get(f"bootstrap:{node_id}")
    bootstrap = json.loads(bootstrap_raw) if bootstrap_raw else None

    cv_raw = await redis.get(f"cv:{node_id}")
    cv_result = json.loads(cv_raw) if cv_raw else None

    quarantine_status = await get_quarantine_status(node_id)
    history = await get_trust_history(node_id, limit=10)

    return {
        "node_id": node_id,
        "trust_score": trust_score,
        "bootstrap": bootstrap,
        "quarantine": quarantine_status,
        "cross_validation": cv_result,
        "recent_history": history,
    }