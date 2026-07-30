"""Integration tests for end-to-end routing through the load balancer."""

import httpx


LOAD_BALANCER_URL = "http://localhost:8000"


def test_health_endpoints() -> None:
    """LB health endpoint should respond correctly."""
    response = httpx.get(f"{LOAD_BALANCER_URL}/health", timeout=5.0)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "load_balancer"}


def test_round_robin_routing_across_all_nodes() -> None:
    """Repeated requests should rotate across all 3 nodes."""
    seen_nodes: list[str] = []

    for _ in range(6):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "test", "data": "hello"},
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["node_id"] in {"node_1", "node_2", "node_3"}

        seen_nodes.append(data["node_id"])

    assert set(seen_nodes) == {"node_1", "node_2", "node_3"}