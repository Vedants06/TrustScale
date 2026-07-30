"""Baseline load test profile for TrustScale."""

from locust import HttpUser, between, task


class BaselineTrafficUser(HttpUser):
    """Simple baseline load profile against the load balancer."""

    wait_time = between(0.1, 0.5)
    host = "http://localhost:8000"

    @task(1)
    def health_check(self) -> None:
        """Send occasional health checks."""
        self.client.get("/health")

    @task(5)
    def send_work(self) -> None:
        """Send normal work traffic through the load balancer."""
        self.client.post(
            "/work",
            json={"task": "baseline", "data": "phase9"},
        )