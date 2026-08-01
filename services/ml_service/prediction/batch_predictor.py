"""Batch prediction for multiple nodes."""

from shared.contracts.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionResponse,
)
from services.ml_service.prediction.predictor import predict_single
from shared.utils.logger import get_logger

logger = get_logger("batch_predictor")


def predict_batch(request: BatchPredictionRequest) -> BatchPredictionResponse:
    """Return predictions for multiple nodes.

    Args:
        request: Batch prediction request.

    Returns:
        Batch prediction response with per-node predictions.
    """
    predictions: dict[str, PredictionResponse] = {}

    for item in request.requests:
        predictions[item.node_id] = predict_single(item)

    logger.info(
        "Batch prediction complete",
        total_nodes=len(predictions),
    )

    return BatchPredictionResponse(predictions=predictions)