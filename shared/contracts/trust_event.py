"""Trust event contracts for tracking node trust changes."""

from enum import Enum

from pydantic import BaseModel, Field


class TrustEventType(str, Enum):
    """Types of trust-affecting events."""

    REPORT_VERIFIED = "report_verified"
    SIGNATURE_INVALID = "signature_invalid"
    TIMESTAMP_STALE = "timestamp_stale"
    METRIC_DISCREPANCY = "metric_discrepancy"
    QUARANTINED = "quarantined"
    RESTORED = "restored"
    HONEST_BEHAVIOR = "honest_behavior"
    COLLUSION_DETECTED = "collusion_detected"
    BOOTSTRAP_PERIOD = "bootstrap_period"


class TrustEvent(BaseModel):
    """A single trust-affecting event."""

    node_id: str
    event_type: TrustEventType
    timestamp: int
    trust_score_before: float = Field(ge=0.0, le=1.0)
    trust_score_after: float = Field(ge=0.0, le=1.0)
    delta: float
    details: str


class NodeTrustStatus(BaseModel):
    """Current trust status of a node."""

    node_id: str
    current_trust_score: float = Field(ge=0.0, le=1.0)
    is_quarantined: bool
    is_in_bootstrap: bool
    total_events: int
    quarantine_count: int
    last_event: TrustEvent | None = None
    quarantine_since: int | None = None
    honest_reports_count: int = 0