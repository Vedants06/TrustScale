"""In-process request tracking for accurate node metrics."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass

from shared.utils.logger import get_logger

logger = get_logger("request_tracker")


@dataclass(slots=True)
class RequestRecord:
    """Single completed request timing record."""

    timestamp: float
    duration_ms: float


class RequestTracker:
    """Track active requests and recent response times."""

    def __init__(self, history_window_seconds: int = 10) -> None:
        self._active_count: int = 0
        self._lock = asyncio.Lock()
        self._history: deque[RequestRecord] = deque(maxlen=5000)
        self._history_window = history_window_seconds
        self._total_requests: int = 0
        self._start_time: float = time.time()

    async def request_started(self) -> None:
        """Mark a new request as started."""
        async with self._lock:
            self._active_count += 1

    async def request_completed(self, duration_ms: float) -> None:
        """Mark a request as completed and record its duration."""
        async with self._lock:
            self._active_count = max(0, self._active_count - 1)
            self._total_requests += 1
            self._history.append(
                RequestRecord(
                    timestamp=time.time(),
                    duration_ms=duration_ms,
                )
            )

    @property
    def active_requests(self) -> int:
        """Current number of in-flight requests."""
        return self._active_count

    @property
    def total_requests(self) -> int:
        """Total requests processed since startup."""
        return self._total_requests

    def get_recent_requests_count(self, window_seconds: int = 5) -> int:
        """Count requests completed in the last N seconds."""
        now = time.time()
        count = 0
        for record in reversed(self._history):
            if now - record.timestamp > window_seconds:
                break
            count += 1
        return count

    def get_average_response_time_ms(self, window_seconds: int = 5) -> float:
        """Average response time of recent requests."""
        now = time.time()
        recent_durations: list[float] = []

        for record in reversed(self._history):
            if now - record.timestamp > window_seconds:
                break
            recent_durations.append(record.duration_ms)

        if not recent_durations:
            return 0.0

        return sum(recent_durations) / len(recent_durations)

    @property
    def uptime_seconds(self) -> int:
        """Seconds since tracker started."""
        return int(time.time() - self._start_time)


# Global singleton
tracker = RequestTracker()