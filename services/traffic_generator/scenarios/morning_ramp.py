"""Morning-ramp traffic pattern for Locust."""

import os

from locust import LoadTestShape


class MorningRampShape(LoadTestShape):
    """Gradually increase users, then hold steady for a period."""

    start_users = int(os.getenv("MORNING_RAMP_START_USERS", "1"))
    target_users = int(os.getenv("MORNING_RAMP_TARGET_USERS", "20"))
    spawn_rate = float(os.getenv("MORNING_RAMP_SPAWN_RATE", "2"))
    ramp_duration_seconds = int(os.getenv("MORNING_RAMP_DURATION_SECONDS", "180"))
    hold_duration_seconds = int(os.getenv("MORNING_RAMP_HOLD_SECONDS", "120"))

    def tick(self) -> tuple[int, float] | None:
        """Return ramped user count based on elapsed time."""
        run_time = self.get_run_time()

        if run_time < self.ramp_duration_seconds:
            progress = run_time / self.ramp_duration_seconds
            current_users = int(
                self.start_users
                + (self.target_users - self.start_users) * progress
            )
            return max(current_users, self.start_users), self.spawn_rate

        if run_time < self.ramp_duration_seconds + self.hold_duration_seconds:
            return self.target_users, self.spawn_rate

        return None