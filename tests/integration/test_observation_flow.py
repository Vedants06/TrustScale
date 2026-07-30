"""Integration test for load-balanced traffic producing observation summaries."""

import httpx
import redis

LOAD_BALANCER_URL = "http://localhost:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NODE_IDS = ["node_1", "node_2", "node_3"]


def test_observation_summaries_are_created_under_traffic() -> None:
    """Repeated traffic through the LB should create Redis observation summaries."""
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )

    # Clear previous observation summaries so this test is deterministic
    for node_id in NODE_IDS:
        redis_client.delete(f"observation:summary:{node_id}")

    # Send enough requests to reach all nodes
    for _ in range(12):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "observe", "data": "phase9"},
            timeout=5.0,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["node_id"] in NODE_IDS

    # Verify all nodes now have observation summaries
    nodes_with_summaries = 0

    for node_id in NODE_IDS:
        summary = redis_client.hgetall(f"observation:summary:{node_id}")

        if summary:
            assert "last_duration_ms" in summary
            assert "last_observed_at" in summary
            assert "total_requests_observed" in summary
            assert float(summary["last_duration_ms"]) > 0
            assert int(summary["last_observed_at"]) > 0
            assert int(summary["total_requests_observed"]) >= 1
            nodes_with_summaries += 1

    assert nodes_with_summaries == len(NODE_IDS), (
        f"Expected summaries for all {len(NODE_IDS)} nodes, "
        f"but only found {nodes_with_summaries}"
    )