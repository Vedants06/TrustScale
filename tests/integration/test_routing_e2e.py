"""Integration tests for end-to-end routing through the load balancer."""

import httpx

LOAD_BALANCER_URL = "http://localhost:8000"
NODE_IDS = {"node_1", "node_2", "node_3"}


def test_health_endpoints() -> None:
    """LB health endpoint should respond correctly."""
    response = httpx.get(f"{LOAD_BALANCER_URL}/health", timeout=5.0)

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "load_balancer"}


def test_routing_reaches_all_nodes() -> None:
    """Repeated requests should reach at least 2 nodes with real predictions."""
    seen_nodes: list[str] = []

    for _ in range(12):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "test", "data": "hello"},
            timeout=5.0,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["node_id"] in NODE_IDS

        seen_nodes.append(data["node_id"])

    assert len(set(seen_nodes)) >= 2, (
        f"Expected at least 2 nodes reached, but only saw: {set(seen_nodes)}"
    )