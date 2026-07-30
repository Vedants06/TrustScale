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

    # Send repeated requests through the load balancer
    for _ in range(9):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "observe", "data": "phase9"},
            timeout=5.0,
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "completed"
        assert payload["node_id"] in NODE_IDS

    total_observed_requests = 0

    # Verify all nodes now have observation summaries
    for node_id in NODE_IDS:
        summary = redis_client.hgetall(f"observation:summary:{node_id}")

        assert summary, f"No observation summary found for {node_id}"
        assert "last_duration_ms" in summary
        assert "last_observed_at" in summary
        assert "total_requests_observed" in summary

        assert float(summary["last_duration_ms"]) > 0
        assert int(summary["last_observed_at"]) > 0
        assert int(summary["total_requests_observed"]) >= 1

        total_observed_requests += int(summary["total_requests_observed"])

    assert total_observed_requests == 9