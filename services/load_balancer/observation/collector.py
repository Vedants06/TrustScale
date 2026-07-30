"""In-memory observation collector for backend request timings."""

from collections import defaultdict, deque
from dataclasses import dataclass
from statistics import mean
from time import time

from shared.utils.logger import get_logger

logger = get_logger("observation_collector")


@dataclass(slots=True)
class ObservationRecord:
    """Single observed backend request timing."""

    timestamp: float
    duration_ms: float


class ObservationCollector:
    """Collect and query recent per-node request observations."""

    def __init__(self, max_records_per_node: int = 1000) -> None:
        self._observations: dict[str, deque[ObservationRecord]] = defaultdict(
            lambda: deque(maxlen=max_records_per_node)
        )

    def record_request(self, node_id: str, duration_ms: float) -> None:
        """Record a request duration for a node."""
        record = ObservationRecord(timestamp=time(), duration_ms=duration_ms)
        self._observations[node_id].append(record)

        logger.debug(
            "Observed backend request",
            node_id=node_id,
            duration_ms=round(duration_ms, 2),
        )

    def get_recent_durations_ms(
        self,
        node_id: str,
        window_seconds: int = 60,
    ) -> list[float]:
        """Get recent durations for a node within the given window."""
        now = time()
        records = self._observations.get(node_id, deque())

        return [
            record.duration_ms
            for record in records
            if now - record.timestamp <= window_seconds
        ]

    def get_request_count(self, node_id: str, window_seconds: int = 60) -> int:
        """Get observed request count for a node in the given window."""
        return len(self.get_recent_durations_ms(node_id, window_seconds))

    def get_average_response_time(self, node_id: str, window_seconds: int = 60) -> float | None:
        """Get average observed response time for a node in the given window."""
        durations = self.get_recent_durations_ms(node_id, window_seconds)
        if not durations:
            return None
        return mean(durations)

    def reset(self) -> None:
        """Clear all collected observations."""
        self._observations.clear()


collector = ObservationCollector()