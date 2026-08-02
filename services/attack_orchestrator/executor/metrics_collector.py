"""Collect scenario-level metrics during attack execution."""

import time
from dataclasses import dataclass, field

import httpx

from shared.utils.logger import get_logger

logger = get_logger("scenario_metrics_collector")

LB_URL = "http://load_balancer:8000"


@dataclass
class ScenarioMetrics:
    """Metrics collected during a scenario run."""

    scenario_id: str
    repetition_number: int
    random_seed: int
    started_at: float = field(default_factory=time.time)
    completed_at: float = 0.0

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0

    latencies_ms: list[float] = field(default_factory=list)

    detection_time_seconds: float | None = None
    nodes_quarantined: list[str] = field(default_factory=list)
    initial_trust_scores: dict[str, float] = field(default_factory=dict)
    final_trust_scores: dict[str, float] = field(default_factory=dict)

    @property
    def avg_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        return sum(self.latencies_ms) / len(self.latencies_ms)

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_latencies = sorted(self.latencies_ms)
        index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests

    @property
    def duration_seconds(self) -> float:
        if self.completed_at == 0.0:
            return time.time() - self.started_at
        return self.completed_at - self.started_at

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "repetition_number": self.repetition_number,
            "random_seed": self.random_seed,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": round(self.duration_seconds, 2),
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": round(self.success_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "detection_time_seconds": self.detection_time_seconds,
            "nodes_quarantined": self.nodes_quarantined,
            "initial_trust_scores": self.initial_trust_scores,
            "final_trust_scores": self.final_trust_scores,
        }


async def get_node_trust_score(node_id: str) -> float | None:
    """Fetch current trust score for a node from the LB API."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{LB_URL}/nodes/{node_id}/trust",
                timeout=5.0,
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("trust_score")
    except Exception as error:
        logger.warning(
            "Failed to fetch trust score",
            node_id=node_id,
            error=str(error),
        )
    return None


async def send_work_request(
    metrics: ScenarioMetrics,
    intensity: int = 1000,
) -> bool:
    """Send a work request through the LB and record metrics."""
    start = time.perf_counter()

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LB_URL}/work",
                json={"task": "attack_scenario", "data": "load_test", "intensity": intensity},
                timeout=10.0,
            )

        duration_ms = (time.perf_counter() - start) * 1000
        metrics.latencies_ms.append(duration_ms)
        metrics.total_requests += 1

        if response.status_code == 200:
            metrics.successful_requests += 1
            return True
        else:
            metrics.failed_requests += 1
            return False

    except Exception:
        duration_ms = (time.perf_counter() - start) * 1000
        metrics.latencies_ms.append(duration_ms)
        metrics.total_requests += 1
        metrics.failed_requests += 1
        return False