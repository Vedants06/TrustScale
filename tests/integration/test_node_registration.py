"""Integration tests for node registration and cluster visibility."""

import httpx


LOAD_BALANCER_URL = "http://localhost:8000"


def test_registered_nodes_are_visible() -> None:
    """Load balancer should list all active nodes."""
    response = httpx.get(f"{LOAD_BALANCER_URL}/nodes", timeout=5.0)

    assert response.status_code == 200
    data = response.json()

    assert "nodes" in data
    assert sorted(data["nodes"]) == ["node_1", "node_2", "node_3"]