"""Locust load generation configuration."""

from locust import HttpUser, task, between


class TrustScaleUser(HttpUser):
    """Simulated user for TrustScale load testing."""

    wait_time = between(0.5, 2.0)
    host = "http://localhost:8000"

    @task
    def health_check(self):
        """Check load balancer health."""
        self.client.get("/health")

    @task(3)
    def send_work(self):
        """Send work request through load balancer."""
        self.client.post("/work", json={"task": "process", "data": "test"})