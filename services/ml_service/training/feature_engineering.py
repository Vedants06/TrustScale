"""Feature engineering for the LSTM load prediction model."""

import numpy as np
import pandas as pd

from shared.utils.logger import get_logger

logger = get_logger("feature_engineering")

# Composite load formula weights from PRD
CPU_WEIGHT = 0.5
ACTIVE_REQUESTS_WEIGHT = 0.3
RESPONSE_TIME_WEIGHT = 0.2

# Normalization constants
MAX_ACTIVE_REQUESTS = 50.0
MAX_RESPONSE_TIME_MS = 1000.0


def compute_composite_load(
    cpu_percent: float,
    active_requests: float,
    response_time_ms: float,
) -> float:
    """Compute composite load score from raw metrics.

    Formula from PRD:
        load = 0.5 × normalized_cpu +
               0.3 × normalized_active_requests +
               0.2 × normalized_response_time

    Args:
        cpu_percent: CPU usage 0-100.
        active_requests: Number of active requests.
        response_time_ms: Average response time in milliseconds.

    Returns:
        Composite load score between 0.0 and 1.0.
    """
    normalized_cpu = cpu_percent / 100.0
    normalized_requests = min(active_requests / MAX_ACTIVE_REQUESTS, 1.0)
    normalized_response_time = min(response_time_ms / MAX_RESPONSE_TIME_MS, 1.0)

    load = (
        CPU_WEIGHT * normalized_cpu
        + ACTIVE_REQUESTS_WEIGHT * normalized_requests
        + RESPONSE_TIME_WEIGHT * normalized_response_time
    )

    return float(np.clip(load, 0.0, 1.0))


def add_composite_load_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add composite load column to a metrics DataFrame.

    Args:
        df: DataFrame with cpu_percent, active_requests, response_time_ms columns.

    Returns:
        DataFrame with added composite_load column.
    """
    df = df.copy()
    df["composite_load"] = df.apply(
        lambda row: compute_composite_load(
            cpu_percent=row["cpu_percent"],
            active_requests=row["active_requests"],
            response_time_ms=row["response_time_ms"],
        ),
        axis=1,
    )
    return df


def create_sequences(
    data: np.ndarray,
    sequence_length: int = 10,
    prediction_horizon: int = 1,
) -> tuple[np.ndarray, np.ndarray]:
    """Create sliding window sequences for LSTM training.

    Args:
        data: 1D array of composite load values.
        sequence_length: Number of timesteps in each input sequence.
        prediction_horizon: How many steps ahead to predict.

    Returns:
        Tuple of (X, y) where:
            X has shape (n_samples, sequence_length, 1)
            y has shape (n_samples,)
    """
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
    """Prepare training and validation data from a metrics DataFrame.

    Args:
        df: DataFrame with composite_load column.
        sequence_length: Sequence length for LSTM input.
        train_split: Fraction of data for training.

    Returns:
        Tuple of (X_train, y_train, X_val, y_val).
    """
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
    )

    return X_train, y_train, X_val, y_val