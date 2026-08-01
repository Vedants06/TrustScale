"""Integration tests for signed health reports with real metrics."""

import json
import time

import httpx
import redis

LOAD_BALANCER_URL = "http://localhost:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NODE_IDS = ["node_1", "node_2", "node_3"]


def test_all_nodes_are_registered() -> None:
    """All nodes should be registered and active."""
    response = httpx.get(f"{LOAD_BALANCER_URL}/nodes", timeout=5.0)

    assert response.status_code == 200
    data = response.json()

    assert sorted(data["nodes"]) == NODE_IDS


def test_all_nodes_have_real_metrics_in_redis() -> None:
    """All nodes should have real metric snapshots stored in Redis."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    # Wait up to 30 seconds for metrics to appear
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

        assert found, f"No metrics found in Redis for {node_id} after {max_wait}s"

        data = json.loads(raw)

        assert "metrics" in data
        metrics = data["metrics"]

        assert "cpu_percent" in metrics
        assert "memory_percent" in metrics
        assert "active_requests" in metrics
        assert "uptime_seconds" in metrics

        assert metrics["cpu_percent"] >= 0.0
        assert metrics["memory_percent"] >= 0.0
        assert metrics["uptime_seconds"] >= 0

        assert metrics["cpu_percent"] != 30.0, (
            f"node {node_id} still has hardcoded CPU value 30.0"
        )
        assert metrics["active_requests"] != 5, (
            f"node {node_id} still has hardcoded active_requests value 5"
        )


def test_heartbeats_are_accepted_with_real_metrics() -> None:
    """Heartbeats should be verified and accepted by the load balancer."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    for node_id in NODE_IDS:
        raw = redis_client.get(f"metrics:{node_id}")

        if raw is None:
            # Wait a bit for heartbeats to arrive
            time.sleep(10)
            raw = redis_client.get(f"metrics:{node_id}")

        assert raw is not None, f"No heartbeat data found for {node_id}"

        data = json.loads(raw)

        assert data["node_id"] == node_id
        assert data["version"] == "1.0"
        assert data["timestamp"] > 0


def test_prometheus_metrics_endpoint_is_reachable() -> None:
    """Load balancer Prometheus metrics endpoint should be reachable."""
    response = httpx.get(f"{LOAD_BALANCER_URL}/metrics", timeout=5.0)

    assert response.status_code == 200
    assert "trustscale_lb_requests_total" in response.text
    assert "trustscale_lb_request_duration_ms" in response.text


def test_node_prometheus_metrics_endpoint_is_reachable() -> None:
    """Node Prometheus metrics endpoint should be reachable."""
    response = httpx.get("http://localhost:8001/metrics", timeout=5.0)

    assert response.status_code == 200
    assert "trustscale_node_cpu_percent" in response.text
    assert "trustscale_node_memory_percent" in response.text
    assert "trustscale_node_active_requests" in response.text


def test_routing_still_works_with_real_metrics() -> None:
    """Routing should still work correctly with real node metrics."""
    seen_nodes: list[str] = []

    for _ in range(12):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "phase15_check", "data": "real_metrics"},
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["node_id"] in set(NODE_IDS)

        seen_nodes.append(data["node_id"])

    assert len(set(seen_nodes)) >= 2, (
        f"Expected at least 2 nodes reached, but only saw: {set(seen_nodes)}"
    )