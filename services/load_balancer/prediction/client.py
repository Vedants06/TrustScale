"""Client for fetching predictions from the ML service."""

import time

import aiohttp

from services.load_balancer.config.settings import settings
from shared.contracts.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    MetricTimestep,
    PredictionRequest,
    PredictionResponse,
)
from shared.utils.logger import get_logger

logger = get_logger("prediction_client")

FALLBACK_PREDICTED_LOAD = 0.5
FALLBACK_CONFIDENCE = 0.0
FALLBACK_MODEL_VERSION = "fallback"

# In-memory cache of recent metrics per node for prediction requests
_node_recent_metrics: dict[str, list[MetricTimestep]] = {}


def update_node_metrics_cache(
    node_id: str,
    cpu_percent: float,
    active_requests: float,
    response_time_ms: float,
) -> None:
    """Update the in-memory cache of recent metrics for a node.

    Called by the heartbeat handler when a valid report arrives.

    Args:
        node_id: Node identifier.
        cpu_percent: Current CPU percent.
        active_requests: Current active requests count.
        response_time_ms: Current average response time.
    """
    if node_id not in _node_recent_metrics:
        _node_recent_metrics[node_id] = []

    timestep = MetricTimestep(
        timestamp=int(time.time()),
        cpu_percent=cpu_percent,
        memory_percent=0.0,
        active_requests=int(active_requests),
        response_time_ms=response_time_ms,
    )

    _node_recent_metrics[node_id].append(timestep)

    # Keep only last 15 timesteps
    if len(_node_recent_metrics[node_id]) > 15:
        _node_recent_metrics[node_id] = _node_recent_metrics[node_id][-15:]


def _get_recent_metrics_for_node(node_id: str) -> list[MetricTimestep]:
    """Get cached recent metrics for a node.

    Falls back to stub metrics if no real data available.

    Args:
        node_id: Node identifier.

    Returns:
        List of at least 10 MetricTimestep objects.
    """
    cached = _node_recent_metrics.get(node_id, [])

    if len(cached) >= 10:
        return cached[-10:]

    now = int(time.time())
    stub_metrics = [
        MetricTimestep(
            timestamp=now - (10 - i) * 5,
            cpu_percent=0.0,
            memory_percent=0.0,
            active_requests=0,
            response_time_ms=0.0,
        )
        for i in range(10)
    ]

    combined = stub_metrics + cached
    return combined[-10:]


def _fallback_prediction(node_id: str) -> PredictionResponse:
    """Return a safe fallback prediction when ML service is unavailable."""
    return PredictionResponse(
        node_id=node_id,
        predicted_load=FALLBACK_PREDICTED_LOAD,
        confidence=FALLBACK_CONFIDENCE,
        model_version=FALLBACK_MODEL_VERSION,
        predicted_at=int(time.time()),
    )


async def fetch_predictions_for_nodes(
    node_ids: list[str],
) -> dict[str, PredictionResponse]:
    """Fetch load predictions for a list of nodes from the ML service.

    Uses real cached metrics from heartbeats for prediction input.
    Falls back to 0.5 predictions if the ML service is unavailable.

    Args:
        node_ids: List of node IDs to predict for.

    Returns:
        Dictionary mapping node_id to PredictionResponse.
    """
    if not node_ids:
        return {}

    requests = [
        PredictionRequest(
            node_id=node_id,
            recent_metrics=_get_recent_metrics_for_node(node_id),
        )
        for node_id in node_ids
    ]

    batch_request = BatchPredictionRequest(requests=requests)
    url = f"{settings.ml_service_url}/predict/batch"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=batch_request.model_dump(),
                timeout=aiohttp.ClientTimeout(total=5.0),
            ) as response:
                if response.status != 200:
                    logger.warning(
                        "ML service returned non-200 status",
                        status=response.status,
                        url=url,
                    )
                    return {
                        node_id: _fallback_prediction(node_id)
                        for node_id in node_ids
                    }

                raw = await response.json()
                batch_response = BatchPredictionResponse(**raw)

                logger.info(
                    "Real predictions fetched from ML service",
                    total_nodes=len(batch_response.predictions),
                )

                return dict(batch_response.predictions)

    except Exception as error:
        logger.warning(
            "ML service unreachable, using fallback predictions",
            error=str(error),
            url=url,
        )
        return {
            node_id: _fallback_prediction(node_id)
            for node_id in node_ids
        }