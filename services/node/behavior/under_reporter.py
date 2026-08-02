from services.node.behavior.base import BaseBehavior, clamp
from shared.contracts.health_report import NodeMetrics


class UnderReporterBehavior(BaseBehavior):
    """Reports lower load than actual.

    reported_value = real_value * (1 - intensity)
    """

    def apply(self, metrics: NodeMetrics) -> NodeMetrics:
        factor = 1 - self.intensity
        data = metrics.model_dump()

        data["cpu_percent"] = clamp(data["cpu_percent"] * factor, 0.0, 100.0)
        data["total_requests_last_5s"] = max(
            0, round(data["total_requests_last_5s"] * factor)
        )
        data["avg_response_time_ms"] = max(
            0.0, data["avg_response_time_ms"] * factor
        )
        # memory_percent, active_requests, uptime_seconds stay untouched

        return NodeMetrics(**data)