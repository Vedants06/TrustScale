"""Fetch historical metrics from Prometheus for ML training."""

import os
import time
from typing import Any

import pandas as pd
import requests

from shared.utils.logger import get_logger

logger = get_logger("metrics_fetcher")

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
NODE_IDS = ["node_1", "node_2", "node_3"]


def fetch_metric_range(
    metric_name: str,
    start_time: float,
    end_time: float,
    step: str = "5s",
) -> dict[str, Any]:
    """Fetch a metric range from Prometheus."""
    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {
        "query": metric_name,
        "start": start_time,
        "end": end_time,
        "step": step,
    }

    response = requests.get(url, params=params, timeout=10.0)
    response.raise_for_status()
    return response.json()


def fetch_node_metrics_dataframe(
    node_id: str,
    duration_minutes: int = 30,
    step: str = "5s",
) -> pd.DataFrame:
    """Fetch recent metrics for a node and return as DataFrame.

    Uses response time and request count as primary signals
    because these work correctly in Docker/WSL2 environments.

    Args:
        node_id: Node identifier.
        duration_minutes: How many minutes of history to fetch.
        step: Scrape step interval.

    Returns:
        DataFrame with columns:
        timestamp, cpu_percent, active_requests, response_time_ms
    """
    end_time = time.time()
    start_time = end_time - (duration_minutes * 60)

    metrics_to_fetch = {
        "cpu_percent": f'trustscale_node_cpu_percent{{node_id="{node_id}"}}',
        "active_requests": f'trustscale_node_requests_last_30s{{node_id="{node_id}"}}',
        "response_time_ms": f'trustscale_node_avg_response_time_ms{{node_id="{node_id}"}}',
    }

    series: dict[str, pd.Series] = {}

    for metric_key, query in metrics_to_fetch.items():
        try:
            result = fetch_metric_range(query, start_time, end_time, step)
            data = result.get("data", {}).get("result", [])

            if not data:
                logger.warning(
                    "No data for metric",
                    node_id=node_id,
                    metric=metric_key,
                )
                continue

            values = data[0].get("values", [])
            if not values:
                continue

            timestamps = [float(v[0]) for v in values]
            metric_values = [float(v[1]) for v in values]

            series[metric_key] = pd.Series(
                metric_values,
                index=pd.to_datetime(timestamps, unit="s"),
            )

        except Exception as error:
            logger.error(
                "Failed to fetch metric",
                node_id=node_id,
                metric=metric_key,
                error=str(error),
            )

    if len(series) < 2:
        logger.warning(
            "Insufficient metrics fetched for node",
            node_id=node_id,
            fetched=list(series.keys()),
        )
        return pd.DataFrame()

    df = pd.DataFrame(series)
    df = df.dropna()
    df = df.reset_index()
    df = df.rename(columns={"index": "timestamp"})

    # Fill missing cpu_percent with 0 if not available
    if "cpu_percent" not in df.columns:
        df["cpu_percent"] = 0.0

    # Fill missing response_time_ms with 0 if not available
    if "response_time_ms" not in df.columns:
        df["response_time_ms"] = 0.0

    # Fill missing active_requests with 0 if not available
    if "active_requests" not in df.columns:
        df["active_requests"] = 0.0

    logger.info(
        "Metrics fetched for node",
        node_id=node_id,
        rows=len(df),
        duration_minutes=duration_minutes,
        response_time_max=float(df["response_time_ms"].max()),
        requests_max=float(df["active_requests"].max()),
    )

    return df


def fetch_all_nodes_training_data(
    duration_minutes: int = 30,
) -> dict[str, pd.DataFrame]:
    """Fetch training data for all nodes."""
    all_data: dict[str, pd.DataFrame] = {}

    for node_id in NODE_IDS:
        df = fetch_node_metrics_dataframe(
            node_id=node_id,
            duration_minutes=duration_minutes,
        )

        if not df.empty:
            all_data[node_id] = df
        else:
            logger.warning("Empty data for node, skipping", node_id=node_id)

    return all_data