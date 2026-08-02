from abc import ABC, abstractmethod
from shared.contracts.health_report import NodeMetrics


def clamp(value: float, low: float, high: float) -> float:
    """Keep a value inside a valid range."""
    return max(low, min(high, value))


class BaseBehavior(ABC):
    """Abstract base class for node behavior modes."""

    def __init__(self, intensity: float = 0.0):
        self.intensity = intensity

    @abstractmethod
    def apply(self, metrics: NodeMetrics) -> NodeMetrics:
        """Take real metrics and return the metrics that should be reported."""
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self.__class__.__name__