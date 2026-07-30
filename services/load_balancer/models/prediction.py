"""Local prediction representation for the load balancer."""

from dataclasses import dataclass


@dataclass(slots=True)
class NodePrediction:
    """Resolved prediction for a single node."""

    node_id: str
    predicted_load: float
    confidence: float
    is_fallback: bool