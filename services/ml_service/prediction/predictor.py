"""Real LSTM-based load predictor for the ML service."""

import time
from pathlib import Path

import numpy as np
import torch

from services.ml_service.config.model_config import (
    LSTM_DROPOUT,
    LSTM_HIDDEN_SIZE,
    LSTM_INPUT_SIZE,
    LSTM_NUM_LAYERS,
    SEQUENCE_LENGTH,
)
from services.ml_service.models.lstm_model import LSTMLoadPredictor
from services.ml_service.training.feature_engineering import compute_composite_load
from shared.contracts.prediction import (
    PredictionRequest,
    PredictionResponse,
)
from shared.utils.logger import get_logger

logger = get_logger("ml_predictor")

STUB_MODEL_VERSION = "stub-v0"
REAL_MODEL_VERSION = "v1"
MODEL_PATH = Path("research/data/models/lstm_v1.pt")

_model: LSTMLoadPredictor | None = None
_model_version: str = STUB_MODEL_VERSION


def load_model() -> bool:
    """Load the trained LSTM model from disk.

    Returns:
        True if model loaded successfully, False otherwise.
    """
    global _model, _model_version

    if not MODEL_PATH.exists():
        logger.warning(
            "Model file not found, using stub predictions",
            path=str(MODEL_PATH),
        )
        return False

    try:
        model = LSTMLoadPredictor(
            input_size=LSTM_INPUT_SIZE,
            hidden_size=LSTM_HIDDEN_SIZE,
            num_layers=LSTM_NUM_LAYERS,
            dropout=LSTM_DROPOUT,
        )

        model.load_state_dict(
            torch.load(MODEL_PATH, weights_only=True, map_location="cpu")
        )
        model.eval()

        _model = model
        _model_version = REAL_MODEL_VERSION

        logger.info(
            "LSTM model loaded successfully",
            version=_model_version,
            path=str(MODEL_PATH),
        )
        return True

    except Exception as error:
        logger.error(
            "Failed to load model, using stub predictions",
            error=str(error),
        )
        return False


def _prepare_input(request: PredictionRequest) -> np.ndarray:
    """Convert recent metrics into LSTM input sequence.

    Args:
        request: Prediction request with recent metrics.

    Returns:
        NumPy array of shape (1, sequence_length, 1).
    """
    metrics = request.recent_metrics[-SEQUENCE_LENGTH:]

    load_values = [
        compute_composite_load(
            cpu_percent=m.cpu_percent,
            active_requests=m.active_requests,
            response_time_ms=m.response_time_ms,
        )
        for m in metrics
    ]

    while len(load_values) < SEQUENCE_LENGTH:
        load_values.insert(0, load_values[0] if load_values else 0.5)

    sequence = np.array(load_values, dtype=np.float32)
    return sequence.reshape(1, SEQUENCE_LENGTH, 1)


def predict_single(request: PredictionRequest) -> PredictionResponse:
    """Return a load prediction for a single node.

    Uses real LSTM model if available, otherwise returns stub.

    Args:
        request: Prediction request with recent metrics.

    Returns:
        Prediction response with predicted load.
    """
    global _model, _model_version

    if _model is None:
        logger.debug(
            "No model loaded, returning stub prediction",
            node_id=request.node_id,
        )
        return PredictionResponse(
            node_id=request.node_id,
            predicted_load=0.5,
            confidence=0.0,
            model_version=STUB_MODEL_VERSION,
            predicted_at=int(time.time()),
        )

    try:
        input_array = _prepare_input(request)
        input_tensor = torch.tensor(input_array, dtype=torch.float32)

        with torch.no_grad():
            output = _model(input_tensor)
            predicted_load = float(output.squeeze().item())

        predicted_load = max(0.0, min(1.0, predicted_load))

        logger.debug(
            "Real LSTM prediction",
            node_id=request.node_id,
            predicted_load=round(predicted_load, 4),
            timesteps=len(request.recent_metrics),
        )

        return PredictionResponse(
            node_id=request.node_id,
            predicted_load=predicted_load,
            confidence=0.85,
            model_version=_model_version,
            predicted_at=int(time.time()),
        )

    except Exception as error:
        logger.error(
            "LSTM inference failed, returning stub",
            node_id=request.node_id,
            error=str(error),
        )
        return PredictionResponse(
            node_id=request.node_id,
            predicted_load=0.5,
            confidence=0.0,
            model_version=STUB_MODEL_VERSION,
            predicted_at=int(time.time()),
        )