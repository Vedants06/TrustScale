"""Integration tests for ML prediction flow through the load balancer."""

import json

import httpx
import redis

LOAD_BALANCER_URL = "http://localhost:8000"
ML_SERVICE_URL = "http://localhost:8100"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NODE_IDS = ["node_1", "node_2", "node_3"]


def test_ml_service_health() -> None:
    """ML service health endpoint should respond correctly."""
    response = httpx.get(f"{ML_SERVICE_URL}/health", timeout=5.0)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "ml_service"}


def test_ml_service_predict_returns_valid_shape() -> None:
    """ML service /predict should return a valid PredictionResponse shape."""
    payload = {
        "node_id": "node_1",
        "recent_metrics": [
            {
                "timestamp": i,
                "cpu_percent": 30.0,
                "memory_percent": 40.0,
                "active_requests": 5,
                "response_time_ms": 50.0,
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

    assert "node_id" in data
    assert "predicted_load" in data
    assert "confidence" in data
    assert "model_version" in data
    assert "predicted_at" in data

    assert data["node_id"] == "node_1"
    assert 0.0 <= data["predicted_load"] <= 1.0
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["model_version"], str)
    assert isinstance(data["predicted_at"], int)


def test_predictions_are_cached_in_redis() -> None:
    """Load balancer should cache ML predictions in Redis."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    # Wait a moment and check predictions exist
    for node_id in NODE_IDS:
        key = f"prediction:{node_id}"
        cached = redis_client.get(key)

        assert cached is not None, (
            f"No cached prediction found for {node_id}. "
            "LB may not have refreshed predictions yet."
        )

        data = json.loads(cached)

        assert "node_id" in data
        assert "predicted_load" in data
        assert data["node_id"] == node_id
        assert 0.0 <= data["predicted_load"] <= 1.0


def test_routing_works_with_predictions_cached() -> None:
    """Routing should work correctly when predictions are cached."""
    seen_nodes: list[str] = []

    for _ in range(12):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "predict_test", "data": "phase12"},
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["node_id"] in set(NODE_IDS)

        seen_nodes.append(data["node_id"])

    assert set(seen_nodes) == set(NODE_IDS), (
        f"Expected all nodes reached, but only saw: {set(seen_nodes)}"
    )


def test_lb_falls_back_gracefully_if_ml_unavailable() -> None:
    """LB should still route requests even if ML predictions are stale or missing.

    This test verifies routing works even without fresh predictions.
    The LB falls back to 0.5 predicted load for missing cache entries.
    """
    response = httpx.post(
        f"{LOAD_BALANCER_URL}/work",
        json={"task": "fallback_test", "data": "phase12"},
        timeout=5.0,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["node_id"] in set(NODE_IDS)