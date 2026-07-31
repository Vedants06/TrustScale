"""Model evaluation utilities."""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from shared.utils.logger import get_logger

logger = get_logger("evaluator")


def evaluate_model(
    model: nn.Module,
    val_loader: DataLoader,
    tolerance: float = 0.10,
) -> dict[str, float]:
    """Evaluate model accuracy on validation data.

    Args:
        model: Trained LSTM model.
        val_loader: Validation data loader.
        tolerance: Acceptable prediction error fraction.

    Returns:
        Dictionary with evaluation metrics.
    """
    model.eval()

    all_predictions: list[float] = []
    all_targets: list[float] = []

    with torch.no_grad():
        for X_batch, y_batch in val_loader:
            predictions = model(X_batch)
            all_predictions.extend(predictions.squeeze().tolist())
            all_targets.extend(y_batch.squeeze().tolist())

    predictions_arr = np.array(all_predictions)
    targets_arr = np.array(all_targets)

    mae = float(np.mean(np.abs(predictions_arr - targets_arr)))
    rmse = float(np.sqrt(np.mean((predictions_arr - targets_arr) ** 2)))

    # Percentage within tolerance
    relative_errors = np.abs(predictions_arr - targets_arr) / (
        np.abs(targets_arr) + 1e-8
    )
    within_tolerance = float(np.mean(relative_errors < tolerance) * 100)

    metrics = {
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "within_10_percent": round(within_tolerance, 2),
        "total_samples": len(all_predictions),
    }

    logger.info(
        "Evaluation complete",
        mae=metrics["mae"],
        rmse=metrics["rmse"],
        within_10_percent=metrics["within_10_percent"],
        total_samples=metrics["total_samples"],
    )

    return metrics