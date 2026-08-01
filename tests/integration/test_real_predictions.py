"""Integration tests for real LSTM prediction integration with load balancer."""

import json
import time

import httpx
import redis

LOAD_BALANCER_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8100"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NODE_IDS = ["node_1", "node_2", "node_3"]


def test_ml_service_uses_real_model() -> None:
    """ML service should be using the real LSTM model, not stub."""
    payload = {
        "node_id": "node_1",
        "recent_metrics": [
            {
                "timestamp": i,
                "cpu_percent": 50.0,
                "memory_percent": 40.0,
                "active_requests": 20,
                "response_time_ms": 300.0,
            }
            for i in range(1, 11)
        ],
    }

    response = httpx.post(
        f"{ML_SERVICE_URL}/predict",
        json=payload,
        timeout=5.0,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["model_version"] != "stub-v0", (
        "ML service is still using stub predictions"
    )
    assert data["confidence"] > 0.0, (
        "Confidence is 0, suggesting fallback predictions"
    )


def test_predictions_differ_for_different_loads() -> None:
    """High load inputs should predict higher load than low load inputs."""
    low_load_payload = {
        "node_id": "node_1",
        "recent_metrics": [
            {
                "timestamp": i,
                "cpu_percent": 1.0,
                "memory_percent": 20.0,
                "active_requests": 0,
                "response_time_ms": 10.0,
            }
            for i in range(1, 11)
        ],
    }

    high_load_payload = {
        "node_id": "node_1",
        "recent_metrics": [
            {
                "timestamp": i,
                "cpu_percent": 80.0,
                "memory_percent": 60.0,
                "active_requests": 100,
                "response_time_ms": 800.0,
            }
            for i in range(1, 11)
        ],
    }

    low_response = httpx.post(
        f"{ML_SERVICE_URL}/predict",
        json=low_load_payload,
        timeout=5.0,
    )

    high_response = httpx.post(
        f"{ML_SERVICE_URL}/predict",
        json=high_load_payload,
        timeout=5.0,
    )

    low_data = low_response.json()
    high_data = high_response.json()

    assert low_data["predicted_load"] < high_data["predicted_load"], (
        f"Low load prediction ({low_data['predicted_load']}) "
        f"should be less than high load prediction ({high_data['predicted_load']})"
    )


def test_cached_predictions_use_real_model() -> None:
    """Cached predictions in Redis should come from the real model."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    # Wait for prediction refresh cycle
    max_wait = 45
    interval = 5

    found = False
    for _ in range(max_wait // interval):
        raw = redis_client.get("prediction:node_1")
        if raw is not None:
            data = json.loads(raw)
            if data.get("model_version") != "stub-v0":
                found = True
                break
        time.sleep(interval)

    assert found, (
        "Cached predictions are still using stub model after waiting"
    )


def test_routing_works_with_real_predictions() -> None:
    """Routing should function correctly with real LSTM predictions.

    With real predictions, nodes may receive unequal traffic
    based on their predicted load. This is correct behavior.
    The test verifies routing works and reaches at least 2 nodes.
    """
    seen_nodes: list[str] = []

    for _ in range(12):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "phase18_check", "data": "real_predictions"},
            timeout=10.0,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["node_id"] in set(NODE_IDS)

        seen_nodes.append(data["node_id"])

    # With real predictions, traffic may not be perfectly even
    # but at least 2 nodes should receive traffic
    assert len(set(seen_nodes)) >= 2, (
        f"Expected at least 2 nodes reached, but only saw: {set(seen_nodes)}"
    )


def test_heartbeats_feed_prediction_cache() -> None:
    """Heartbeats should feed real metrics into the prediction client cache."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    # Wait for metrics to appear
    max_wait = 30
    interval = 2

    for node_id in NODE_IDS:
        found = False
        for _ in range(max_wait // interval):
            raw = redis_client.get(f"metrics:{node_id}")
            if raw is not None:
                found = True
                break
            time.sleep(interval)

        assert found, f"No metrics found for {node_id} after {max_wait}s"

        data = json.loads(raw)
        assert data["node_id"] == node_id
        assert "metrics" in data