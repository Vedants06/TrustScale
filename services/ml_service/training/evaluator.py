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
    tolerance: float = 0.05,
) -> dict[str, float]:
    """Evaluate model accuracy on validation data.

    Args:
        model: Trained LSTM model.
        val_loader: Validation data loader.
        tolerance: Absolute prediction error tolerance (on 0-1 scale).

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

    # Absolute tolerance check (better for near-zero values)
    absolute_errors = np.abs(predictions_arr - targets_arr)
    within_absolute_tolerance = float(
        np.mean(absolute_errors < tolerance) * 100
    )

    # Relative tolerance check (meaningful only when actual > 0.1)
    high_load_mask = targets_arr > 0.1
    if high_load_mask.sum() > 0:
        relative_errors = np.abs(
            predictions_arr[high_load_mask] - targets_arr[high_load_mask]
        ) / targets_arr[high_load_mask]
        within_relative_tolerance = float(
            np.mean(relative_errors < 0.10) * 100
        )
    else:
        within_relative_tolerance = 0.0

    metrics = {
        "mae": round(mae, 6),
        "rmse": round(rmse, 6),
        "within_absolute_05": round(within_absolute_tolerance, 2),
        "within_10_percent_highload": round(within_relative_tolerance, 2),
        "total_samples": len(all_predictions),
        "high_load_samples": int(high_load_mask.sum()),
    }

    logger.info(
        "Evaluation complete",
        mae=metrics["mae"],
        rmse=metrics["rmse"],
        within_absolute_05=metrics["within_absolute_05"],
        within_10_percent_highload=metrics["within_10_percent_highload"],
        total_samples=metrics["total_samples"],
    )

    return metrics