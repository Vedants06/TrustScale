"""Colluder behavior for coordinated Byzantine attacks."""

from services.node.behavior.base import BaseBehavior, clamp
from shared.contracts.health_report import NodeMetrics


class ColluderBehavior(BaseBehavior):
    """Coordinated Byzantine behavior for collusion attacks.

    Behaves like under_reporter — reduces reported metrics by the
    given intensity. The difference from under_reporter is intent:
    colluders are meant to be triggered simultaneously across multiple
    nodes to test the trust engine against coordinated attacks.

    Formula:
        reported_value = real_value * (1 - intensity)
    """

    def apply(self, metrics: NodeMetrics) -> NodeMetrics:
        factor = 1 - self.intensity
        data = metrics.model_dump()

        data["cpu_percent"] = clamp(
            data["cpu_percent"] * factor, 0.0, 100.0
        )
        data["total_requests_last_5s"] = max(
            0, round(data["total_requests_last_5s"] * factor)
        )
        data["avg_response_time_ms"] = max(
            0.0, data["avg_response_time_ms"] * factor
        )

        return NodeMetrics(**data)