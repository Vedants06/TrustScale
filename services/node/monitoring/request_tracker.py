"""In-process request and CPU tracking for accurate node metrics."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass

import psutil

from shared.utils.logger import get_logger

logger = get_logger("request_tracker")


@dataclass(slots=True)
class RequestRecord:
    """Single completed request timing record."""

    timestamp: float
    duration_ms: float


class CPUTracker:
    """Track real CPU usage using process-level CPU times.

    Works correctly inside Docker containers on Windows/WSL2
    where psutil.cpu_percent() returns near-zero values.
    """

    def __init__(self, smoothing_window: int = 5) -> None:
        self._process = psutil.Process()
        self._last_cpu_times = self._process.cpu_times()
        self._last_wall_time = time.perf_counter()
        self._cpu_history: deque[float] = deque(maxlen=smoothing_window)
        self._cpu_count = psutil.cpu_count(logical=True) or 1

    def get_cpu_percent(self) -> float:
        """Get current CPU usage as a percentage.

        Uses process-level CPU time delta for accuracy in containers.

        Returns:
            CPU usage percentage (0.0 to 100.0).
        """
        try:
            current_cpu_times = self._process.cpu_times()
            current_wall_time = time.perf_counter()

            wall_elapsed = current_wall_time - self._last_wall_time

            if wall_elapsed < 0.01:
                if self._cpu_history:
                    return self._cpu_history[-1]
                return 0.0

            cpu_elapsed = (
                (current_cpu_times.user - self._last_cpu_times.user)
                + (current_cpu_times.system - self._last_cpu_times.system)
            )

            self._last_cpu_times = current_cpu_times
            self._last_wall_time = current_wall_time

            cpu_percent = (cpu_elapsed / wall_elapsed) * 100.0
            cpu_percent = min(100.0, max(0.0, cpu_percent))

            self._cpu_history.append(cpu_percent)

            smoothed = sum(self._cpu_history) / len(self._cpu_history)
            return round(smoothed, 2)

        except Exception as error:
            logger.warning("CPU tracking error", error=str(error))
            return 0.0


class RequestTracker:
    """Track active requests and recent response times."""

    def __init__(self, history_window_seconds: int = 10) -> None:
        self._active_count: int = 0
        self._lock = asyncio.Lock()
        self._history: deque[RequestRecord] = deque(maxlen=5000)
        self._history_window = history_window_seconds
        self._total_requests: int = 0
        self._start_time: float = time.time()
        self.cpu_tracker = CPUTracker()

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

        return round(sum(recent_durations) / len(recent_durations), 2)

    def get_p95_response_time_ms(self, window_seconds: int = 5) -> float:
        """P95 response time of recent requests."""
        now = time.time()
        recent_durations: list[float] = []

        for record in reversed(self._history):
            if now - record.timestamp > window_seconds:
                break
            recent_durations.append(record.duration_ms)

        if not recent_durations:
            return 0.0

        sorted_durations = sorted(recent_durations)
        index = int(len(sorted_durations) * 0.95)
        return round(sorted_durations[min(index, len(sorted_durations) - 1)], 2)

    @property
    def uptime_seconds(self) -> int:
        """Seconds since tracker started."""
        return int(time.time() - self._start_time)


tracker = RequestTracker()