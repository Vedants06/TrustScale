"""Prediction endpoints for the ML service."""

from fastapi import APIRouter

from services.ml_service.prediction.predictor import predict_batch, predict_single
from shared.contracts.prediction import (
    BatchPredictionRequest,
    BatchPredictionResponse,
    PredictionRequest,
    PredictionResponse,
)

router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=PredictionResponse)
async def predict(request: PredictionRequest) -> PredictionResponse:
    """Return a stub load prediction for one node."""
    return predict_single(request)


@router.post("/batch", response_model=BatchPredictionResponse)
async def batch_predict(
    request: BatchPredictionRequest,
) -> BatchPredictionResponse:
    """Return stub load predictions for multiple nodes."""
    return predict_batch(request)