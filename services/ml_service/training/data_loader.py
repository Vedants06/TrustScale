"""Data loading utilities for LSTM training."""

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from shared.utils.logger import get_logger

logger = get_logger("data_loader")


def create_data_loaders(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    batch_size: int = 32,
) -> tuple[DataLoader, DataLoader]:
    """Create PyTorch DataLoaders for training and validation.

    Args:
        X_train: Training input sequences.
        y_train: Training target values.
        X_val: Validation input sequences.
        y_val: Validation target values.
        batch_size: Batch size for training.

    Returns:
        Tuple of (train_loader, val_loader).
    """
    X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
    y_train_tensor = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
    y_val_tensor = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)

    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    val_dataset = TensorDataset(X_val_tensor, y_val_tensor)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    logger.info(
        "DataLoaders created",
        train_batches=len(train_loader),
        val_batches=len(val_loader),
        batch_size=batch_size,
    )

    return train_loader, val_loader