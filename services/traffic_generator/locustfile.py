"""Locust load generation configuration for TrustScale."""

import os
import random

from locust import HttpUser, between, task

TRAFFIC_PATTERN = os.getenv("TRAFFIC_PATTERN", "steady_state").strip().lower()

if TRAFFIC_PATTERN == "morning_ramp":
    from services.traffic_generator.scenarios.morning_ramp import (
        MorningRampShape as TrafficShape,
    )
else:
    from services.traffic_generator.scenarios.steady_state import (
        SteadyStateShape as TrafficShape,
    )


class TrustScaleUser(HttpUser):
    """Simulated user for TrustScale load testing."""

    wait_time = between(0.1, 0.5)
    host = os.getenv("TARGET_URL", "http://localhost:8000")

    @task(1)
    def health_check(self) -> None:
        """Occasional health check request."""
        self.client.get("/health")

    @task(5)
    def send_work(self) -> None:
        """Send work request with CPU-intensive matrix computation."""
        import random
        intensity = random.choice([100, 150, 200, 250, 300])
        self.client.post(
            "/work",
            json={
                "task": "load_test",
                "data": "hello",
                "intensity": intensity,
            },
        )