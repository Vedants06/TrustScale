"""Routing decision contracts for logging load balancer decisions."""

from pydantic import BaseModel, Field


class NodeScoreDetails(BaseModel):
    """Score breakdown for a single node during routing."""

    node_id: str
    predicted_load: float = Field(ge=0.0, le=1.0)
    trust_score: float = Field(ge=0.0, le=1.0)
    combined_score: float
    is_quarantined: bool
    is_eligible: bool


class RoutingDecision(BaseModel):
    """Record of a single routing decision."""

    request_id: str
    timestamp: int
    strategy: str
    all_scores: dict[str, NodeScoreDetails]
    selected_node: str
    rejected_reasons: dict[str, str]