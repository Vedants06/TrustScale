"""Trust-related data models for the load balancer."""

from dataclasses import dataclass, field


@dataclass
class NodeTrustState:
    """In-memory trust state for a node."""

    node_id: str
    trust_score: float = 0.5
    is_quarantined: bool = False
    is_in_bootstrap: bool = True
    honest_reports_count: int = 0
    quarantine_count: int = 0
    total_events: int = 0