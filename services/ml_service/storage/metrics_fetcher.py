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
    """Fetch a metric range from Prometheus.

    Args:
        metric_name: Prometheus metric name.
        start_time: Unix timestamp for range start.
        end_time: Unix timestamp for range end.
        step: Step interval string.

    Returns:
        Prometheus range query result.
    """
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

    Args:
        node_id: Node identifier.
        duration_minutes: How many minutes of history to fetch.
        step: Scrape step interval.

    Returns:
        DataFrame with columns:
        timestamp, cpu_percent, memory_percent,
        active_requests, response_time_ms
    """
    end_time = time.time()
    start_time = end_time - (duration_minutes * 60)

    metrics_to_fetch = {
        "cpu_percent": f'trustscale_node_cpu_percent{{node_id="{node_id}"}}',
        "memory_percent": f'trustscale_node_memory_percent{{node_id="{node_id}"}}',
        "active_requests": f'trustscale_node_active_requests{{node_id="{node_id}"}}',
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

    if not series:
        logger.warning("No metrics fetched for node", node_id=node_id)
        return pd.DataFrame()

    df = pd.DataFrame(series)
    df = df.dropna()
    df = df.reset_index()
    df = df.rename(columns={"index": "timestamp"})

    # Add placeholder response time from LB observation if available
    df["response_time_ms"] = 100.0

    logger.info(
        "Metrics fetched for node",
        node_id=node_id,
        rows=len(df),
        duration_minutes=duration_minutes,
    )

    return df


def fetch_all_nodes_training_data(
    duration_minutes: int = 30,
) -> dict[str, pd.DataFrame]:
    """Fetch training data for all nodes.

    Args:
        duration_minutes: History duration in minutes.

    Returns:
        Dictionary mapping node_id to DataFrame.
    """
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