"""Feature engineering for the LSTM load prediction model."""

import numpy as np
import pandas as pd

from shared.utils.logger import get_logger

logger = get_logger("feature_engineering")

# Composite load formula weights
# Response time is weighted most heavily because:
# 1. It is the primary observable signal for load balancers
# 2. It works correctly in containerized environments
# 3. It aligns with production systems (nginx, HAProxy, AWS ALB)
# 4. It is the most direct indicator of node stress
CPU_WEIGHT = 0.2
ACTIVE_REQUESTS_WEIGHT = 0.3
RESPONSE_TIME_WEIGHT = 0.5

# Normalization constants
MAX_ACTIVE_REQUESTS = 50.0
MAX_RESPONSE_TIME_MS = 2000.0


def compute_composite_load(
    cpu_percent: float,
    active_requests: float,
    response_time_ms: float,
) -> float:
    """Compute composite load score from raw metrics.

    Formula (response-time primary):
        load = 0.2 × normalized_cpu +
               0.3 × normalized_active_requests +
               0.5 × normalized_response_time

    Args:
        cpu_percent: CPU usage 0-100.
        active_requests: Number of recent requests in last 5s.
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