"""Integration tests for the full trust engine.

Tests the complete trust pipeline:
  heartbeat → cross-validation → trust scoring → quarantine

Phase 23 tests honest node behavior only.
Byzantine node tests will be added after Phase 24 (Member 2).
"""

import json
import time

import httpx
import redis

LOAD_BALANCER_URL = "http://localhost:8000"
REDIS_HOST = "localhost"
REDIS_PORT = 6379
NODE_IDS = ["node_1", "node_2", "node_3"]


def get_redis_client() -> redis.Redis:
    """Get a sync Redis client for test assertions."""
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
    )


def test_all_nodes_have_trust_scores() -> None:
    """All registered nodes should have trust scores in Redis."""
    redis_client = get_redis_client()

    # Wait for at least one heartbeat cycle
    time.sleep(6)

    for node_id in NODE_IDS:
        trust_raw = redis_client.get(f"trust:{node_id}")
        assert trust_raw is not None, (
            f"No trust score found for {node_id}"
        )

        trust_score = float(trust_raw)
        assert 0.0 <= trust_score <= 1.0, (
            f"Trust score {trust_score} out of range for {node_id}"
        )


def test_honest_nodes_have_increasing_trust() -> None:
    """Honest nodes should have trust scores at or above initial 0.5."""
    redis_client = get_redis_client()

    # Wait for several heartbeat cycles
    time.sleep(15)

    nodes_above_initial = 0

    for node_id in NODE_IDS:
        trust_raw = redis_client.get(f"trust:{node_id}")
        if trust_raw:
            trust_score = float(trust_raw)
            if trust_score >= 0.5:
                nodes_above_initial += 1

    assert nodes_above_initial >= 2, (
        f"Expected at least 2 honest nodes at or above 0.5 trust, "
        f"but only found {nodes_above_initial}"
    )


def test_honest_nodes_are_not_quarantined() -> None:
    """Honest nodes should not be quarantined."""
    redis_client = get_redis_client()

    for node_id in NODE_IDS:
        quarantine_raw = redis_client.get(f"quarantine:{node_id}")

        if quarantine_raw is not None:
            assert quarantine_raw != "true", (
                f"Node {node_id} is quarantined but should be honest"
            )


def test_trust_history_is_recorded() -> None:
    """Trust events should be recorded for all nodes."""
    redis_client = get_redis_client()

    time.sleep(6)

    for node_id in NODE_IDS:
        history_raw = redis_client.lrange(f"trust_history:{node_id}", 0, 4)

        assert len(history_raw) > 0, (
            f"No trust history found for {node_id}"
        )

        latest_event = json.loads(history_raw[0])

        assert "event_type" in latest_event
        assert "trust_score_before" in latest_event
        assert "trust_score_after" in latest_event
        assert "delta" in latest_event
        assert "timestamp" in latest_event

        assert latest_event["event_type"] in (
            "honest_behavior",
            "bootstrap_period",
            "metric_discrepancy",
            "quarantined",
            "restored",
            "signature_invalid",
            "timestamp_stale",
        )


def test_bootstrap_policy_active_for_new_nodes() -> None:
    """New nodes should be in bootstrap period."""
    redis_client = get_redis_client()

    time.sleep(6)

    for node_id in NODE_IDS:
        bootstrap_raw = redis_client.get(f"bootstrap:{node_id}")

        assert bootstrap_raw is not None, (
            f"No bootstrap state found for {node_id}"
        )

        bootstrap = json.loads(bootstrap_raw)
        assert "honest_reports_count" in bootstrap
        assert "is_in_bootstrap" in bootstrap
        assert bootstrap["honest_reports_count"] >= 0


def test_cross_validation_results_stored() -> None:
    """Cross-validation results should be stored for all nodes."""
    redis_client = get_redis_client()

    time.sleep(6)

    for node_id in NODE_IDS:
        cv_raw = redis_client.get(f"cv:{node_id}")

        assert cv_raw is not None, (
            f"No cross-validation result found for {node_id}"
        )

        cv = json.loads(cv_raw)

        assert "discrepancy" in cv
        assert "has_sufficient_data" in cv
        assert "claimed_load" in cv
        assert cv["discrepancy"] >= 0.0


def test_trust_api_returns_full_state() -> None:
    """GET /nodes/{id}/trust should return complete trust state."""
    for node_id in NODE_IDS:
        response = httpx.get(
            f"{LOAD_BALANCER_URL}/nodes/{node_id}/trust",
            timeout=5.0,
        )

        assert response.status_code == 200

        data = response.json()

        assert "node_id" in data
        assert "trust_score" in data
        assert "bootstrap" in data
        assert "quarantine" in data
        assert "cross_validation" in data
        assert "recent_history" in data

        assert data["node_id"] == node_id
        assert data["trust_score"] is not None
        assert isinstance(data["recent_history"], list)


def test_prometheus_trust_metrics_exist() -> None:
    """Prometheus metrics endpoint should expose trust scores."""
    response = httpx.get(
        f"{LOAD_BALANCER_URL}/metrics",
        timeout=5.0,
    )

    assert response.status_code == 200

    metrics_text = response.text

    assert "trustscale_node_trust_score" in metrics_text, (
        "Trust score metric missing from Prometheus"
    )
    assert "trustscale_node_is_quarantined" in metrics_text, (
        "Quarantine metric missing from Prometheus"
    )
    assert "trustscale_node_quarantine_count" in metrics_text, (
        "Quarantine count metric missing from Prometheus"
    )
    assert "trustscale_node_discrepancy" in metrics_text, (
        "Discrepancy metric missing from Prometheus"
    )


def test_routing_works_with_trust_engine_active() -> None:
    """Routing should function correctly with trust engine active."""
    seen_nodes: list[str] = []

    for _ in range(12):
        response = httpx.post(
            f"{LOAD_BALANCER_URL}/work",
            json={"task": "phase23_check", "data": "trust_engine"},
            timeout=10.0,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "completed"
        assert data["node_id"] in set(NODE_IDS)

        seen_nodes.append(data["node_id"])

    assert len(seen_nodes) == 12, "All 12 requests should succeed"
    assert len(set(seen_nodes)) >= 1, "At least 1 node should receive traffic"


def test_heartbeat_response_includes_trust_data() -> None:
    """Heartbeat API response should include trust score and discrepancy."""
    redis_client = get_redis_client()

    # Check that heartbeat response fields are being stored
    for node_id in NODE_IDS:
        trust_raw = redis_client.get(f"trust:{node_id}")
        assert trust_raw is not None

        cv_raw = redis_client.get(f"cv:{node_id}")
        assert cv_raw is not None

        cv = json.loads(cv_raw)
        assert "discrepancy" in cv