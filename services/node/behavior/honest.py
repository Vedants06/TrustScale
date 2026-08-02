from services.node.behavior.base import BaseBehavior
from shared.contracts.health_report import NodeMetrics


class HonestBehavior(BaseBehavior):
    """Default behavior: reports real metrics completely unchanged."""

    def apply(self, metrics: NodeMetrics) -> NodeMetrics:
        return metrics.model_copy()