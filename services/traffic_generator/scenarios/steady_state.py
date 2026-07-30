"""Steady-state traffic pattern for Locust."""

import os

from locust import LoadTestShape


class SteadyStateShape(LoadTestShape):
    """Maintain a constant number of users for a fixed duration."""

    target_users = int(os.getenv("STEADY_STATE_USERS", "10"))
    spawn_rate = float(os.getenv("STEADY_STATE_SPAWN_RATE", "2"))
    duration_seconds = int(os.getenv("STEADY_STATE_DURATION_SECONDS", "300"))

    def tick(self) -> tuple[int, float] | None:
        """Return steady-state user count until the scenario duration ends."""
        run_time = self.get_run_time()
        if run_time > self.duration_seconds:
            return None

        return self.target_users, self.spawn_rate