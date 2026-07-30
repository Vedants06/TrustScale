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


def _build_stub_metrics(node_id: str) -> PredictionRequest:
    """Build a minimal stub prediction request for a node.

    Used when no real metrics are available yet.
    """
    now = int(time.time())
    stub_metrics = [
        MetricTimestep(
            timestamp=now - (10 - i) * 5,
            cpu_percent=30.0,
            memory_percent=40.0,
            active_requests=5,
            response_time_ms=50.0,
        )
        for i in range(10)
    ]
    return PredictionRequest(node_id=node_id, recent_metrics=stub_metrics)


def _fallback_prediction(node_id: str) -> PredictionResponse:
    """Return a safe fallback prediction when the ML service is unavailable."""
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

    Falls back to 0.5 predictions if the ML service is unavailable.

    Args:
        node_ids: List of node IDs to predict for.

    Returns:
        Dictionary mapping node_id to PredictionResponse.
    """
    if not node_ids:
        return {}

    requests = [_build_stub_metrics(node_id) for node_id in node_ids]
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
                    "Predictions fetched from ML service",
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