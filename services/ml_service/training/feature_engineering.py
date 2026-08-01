"""Feature engineering for the LSTM load prediction model."""

import numpy as np
import pandas as pd

from shared.utils.composite_load import (
    compute_composite_load,
    CPU_WEIGHT,
    ACTIVE_REQUESTS_WEIGHT,
    RESPONSE_TIME_WEIGHT,
    MAX_ACTIVE_REQUESTS,
    MAX_RESPONSE_TIME_MS,
)
from shared.utils.logger import get_logger

logger = get_logger("feature_engineering")


def add_composite_load_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add composite load column to a metrics DataFrame."""
    df = df.copy()
    df["composite_load"] = df.apply(
        lambda row: compute_composite_load(
            cpu_percent=row["cpu_percent"],
            active_requests=row.get("active_requests", 0),
            response_time_ms=row.get("response_time_ms", 0),
        ),
        axis=1,
    )
    return df


def create_sequences(
    data: np.ndarray,
    sequence_length: int = 10,
    prediction_horizon: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Create sliding window sequences for LSTM training."""
    X_list = []
    y_list = []

    for i in range(len(data) - sequence_length - prediction_horizon + 1):
        X_list.append(data[i : i + sequence_length])
        y_list.append(data[i + sequence_length + prediction_horizon - 1])

    X = np.array(X_list, dtype=np.float32).reshape(-1, sequence_length, 1)
    y = np.array(y_list, dtype=np.float32)

    return X, y


def prepare_training_data(
    df: pd.DataFrame,
    sequence_length: int = 10,
    train_split: float = 0.8,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Prepare training and validation data from a metrics DataFrame."""
    if "composite_load" not in df.columns:
        df = add_composite_load_column(df)

    load_values = df["composite_load"].values.astype(np.float32)

    if len(load_values) < sequence_length + 2:
        raise ValueError(
            f"Not enough data for training. "
            f"Need at least {sequence_length + 2} timesteps, "
            f"got {len(load_values)}."
        )

    X, y = create_sequences(load_values, sequence_length)

    split_idx = int(len(X) * train_split)
    X_train = X[:split_idx]
    y_train = y[:split_idx]
    X_val = X[split_idx:]
    y_val = y[split_idx:]

    logger.info(
        "Training data prepared",
        total_sequences=len(X),
        train_sequences=len(X_train),
        val_sequences=len(X_val),
        sequence_length=sequence_length,
        load_min=float(load_values.min()),
        load_max=float(load_values.max()),
        load_mean=float(load_values.mean()),
    )

    return X_train, y_train, X_val, y_val