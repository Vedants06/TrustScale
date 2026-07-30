"""Stub predictor for Phase 10 ML service skeleton."""

from time import time

from shared.contracts.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)
from shared.utils.logger import get_logger

logger = get_logger("ml_predictor")

STUB_MODEL_VERSION = "stub-v0"


def predict_single(request: PredictionRequest) -> PredictionResponse:
    """Return a stub prediction response for a single node.

    This is intentionally hardcoded for Phase 10.
    Real model inference will replace this in later phases.
    """
    logger.info(
        "Stub prediction generated",
        node_id=request.node_id,
        timesteps=len(request.recent_metrics),
    )

    return PredictionResponse(
        node_id=request.node_id,
        predicted_load=0.5,
        confidence=0.8,
        model_version=STUB_MODEL_VERSION,
        predicted_at=int(time()),
    )


def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Return stub predictions for multiple nodes."""
    predictions = {
        item.node_id: predict_single(item)
        for item in request.requests
    }

    logger.info(
        "Stub batch prediction generated",
        total_nodes=len(predictions),
    )

    return BatchPredictionResponse(predictions=predictions)