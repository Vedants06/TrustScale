"""Baseline profiler for establishing per-node response time profiles.

Run from project root while the cluster is running with varied traffic:
    python scripts/baseline_profiler.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import json
import time
from collections import defaultdict

import numpy as np
import requests

from shared.utils.composite_load import compute_composite_load
from shared.utils.logger import get_logger

logger = get_logger("baseline_profiler")

PROMETHEUS_URL = "http://localhost:9090"
REDIS_URL = "redis://localhost:6379"
NODE_IDS = ["node_1", "node_2", "node_3"]
DURATION_MINUTES = 60
LOAD_BUCKET_SIZE = 0.1
TIMESTAMP_ROUND_SECONDS = 5


def fetch_metric_values(
    query: str,
    duration_minutes: int = 60,
    step: str = "5s",
) -> dict[int, float]:
    """Fetch metric values from Prometheus as {rounded_timestamp: value}."""
    end_time = time.time()
    start_time = end_time - (duration_minutes * 60)

    url = f"{PROMETHEUS_URL}/api/v1/query_range"
    params = {
        "query": query,
        "start": start_time,
        "end": end_time,
        "step": step,
    }

    try:
        response = requests.get(url, params=params, timeout=30.0)
        response.raise_for_status()
    except Exception as error:
        logger.error("Prometheus query failed", query=query, error=str(error))
        return {}

    data = response.json().get("data", {}).get("result", [])
    if not data:
        return {}

    values = data[0].get("values", [])
    result = {}
    for v in values:
        rounded_ts = int(float(v[0]) / TIMESTAMP_ROUND_SECONDS) * TIMESTAMP_ROUND_SECONDS
        result[rounded_ts] = float(v[1])

    return result


def build_baseline_profile(node_id: str) -> dict[float, float]:
    """Build a baseline profile for a single node."""
    logger.info("Fetching metrics for baseline profiling", node_id=node_id)

    cpu_by_ts = fetch_metric_values(
        f'trustscale_node_cpu_percent{{node_id="{node_id}"}}'
    )
    req_by_ts = fetch_metric_values(
        f'trustscale_node_requests_last_30s{{node_id="{node_id}"}}'
    )
    rt_by_ts = fetch_metric_values(
        f'trustscale_node_avg_response_time_ms{{node_id="{node_id}"}}'
    )
    p95_by_ts = fetch_metric_values(
        f'trustscale_node_p95_response_time_ms{{node_id="{node_id}"}}'
    )

    logger.info(
        "Metric counts",
        node_id=node_id,
        cpu=len(cpu_by_ts),
        requests=len(req_by_ts),
        response_time=len(rt_by_ts),
        p95=len(p95_by_ts),
    )

    if not cpu_by_ts or not rt_by_ts:
        logger.warning(
            "Insufficient data for profiling",
            node_id=node_id,
        )
        return {}

    # Find timestamps present in at least cpu and response_time
    common_timestamps = sorted(
        set(cpu_by_ts.keys()) & set(rt_by_ts.keys())
    )

    if not common_timestamps:
        # Fallback: align by nearest timestamp
        logger.info("Trying nearest-timestamp alignment", node_id=node_id)
        common_timestamps = sorted(cpu_by_ts.keys())

    if not common_timestamps:
        logger.warning("No usable timestamps", node_id=node_id)
        return {}

    logger.info(
        "Common timestamps found",
        node_id=node_id,
        count=len(common_timestamps),
    )

    # Group observations by load bucket
    buckets: dict[float, list[float]] = defaultdict(list)

    for ts in common_timestamps:
        cpu = cpu_by_ts.get(ts, 0.0)
        active_req = req_by_ts.get(ts, 0.0)
        response_time = rt_by_ts.get(ts, 0.0)
        p95_rt = p95_by_ts.get(ts, response_time)

        if p95_rt <= 0 and response_time > 0:
            p95_rt = response_time * 1.5

        composite_load = compute_composite_load(
            cpu_percent=cpu,
            active_requests=active_req,
            response_time_ms=response_time,
        )

        bucket = round(
            round(composite_load / LOAD_BUCKET_SIZE) * LOAD_BUCKET_SIZE,
            1,
        )
        bucket = max(0.0, min(1.0, bucket))

        if p95_rt > 0:
            buckets[bucket].append(p95_rt)
        elif response_time > 0:
            buckets[bucket].append(response_time)

    # Compute P95 for each bucket
    profile: dict[float, float] = {}

    for bucket_load, response_times in sorted(buckets.items()):
        if len(response_times) >= 2:
            p95 = float(np.percentile(response_times, 95))
            profile[bucket_load] = round(p95, 2)
        elif len(response_times) == 1:
            profile[bucket_load] = round(response_times[0], 2)

    logger.info(
        "Baseline profile built",
        node_id=node_id,
        buckets=len(profile),
        total_observations=len(common_timestamps),
    )

    return profile


def store_profile_in_redis_sync(
    node_id: str,
    profile: dict[float, float],
) -> None:
    """Store a baseline profile in Redis using sync client."""
    import redis as redis_lib

    client = redis_lib.Redis(
        host="localhost",
        port=6379,
        decode_responses=True,
    )

    key = f"baseline:{node_id}"
    serialized = {str(k): v for k, v in profile.items()}
    client.set(key, json.dumps(serialized))
    client.close()

    logger.info("Profile stored in Redis", node_id=node_id, key=key)


def main() -> None:
    """Run baseline profiling for all nodes."""
    logger.info("Starting baseline profiling")

    all_profiles: dict[str, dict[float, float]] = {}

    for node_id in NODE_IDS:
        profile = build_baseline_profile(node_id)

        if profile:
            all_profiles[node_id] = profile
            print(f"\n{node_id} baseline profile:")
            for load_level, p95_ms in sorted(profile.items()):
                print(f"  load={load_level:.1f} → P95={p95_ms:.1f}ms")
        else:
            print(f"\n{node_id}: insufficient data for profiling")
            print("  Make sure Locust traffic has been running for at least 15 minutes")

    if all_profiles:
        for node_id, profile in all_profiles.items():
            store_profile_in_redis_sync(node_id, profile)
        print(f"\nStored {len(all_profiles)} baseline profiles in Redis")
    else:
        print("\nNo profiles could be built.")
        print("Steps to fix:")
        print("1. Start docker-compose up")
        print("2. Let Locust run morning_ramp for 15-20 minutes")
        print("3. Run this script again")

    print("\nBaseline profiling complete.")


if __name__ == "__main__":
    main()