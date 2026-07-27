"""Attack scenario contracts for Byzantine fault injection."""

from enum import Enum

from pydantic import BaseModel, Field


class BehaviorMode(str, Enum):
    """Node behavior modes for attack simulation."""

    HONEST = "honest"
    UNDER_REPORTER = "under_reporter"
    OVER_REPORTER = "over_reporter"
    INTERMITTENT_LIAR = "intermittent_liar"
    COLLUDER = "colluder"


class NodeAttackConfig(BaseModel):
    """Attack configuration for a single node."""

    node_id: str
    behavior: BehaviorMode
    intensity: float = Field(ge=0.0, le=1.0)
    start_at_seconds: int = Field(ge=0)
    duration_seconds: int = Field(ge=1)
    collusion_group_id: str | None = None


class AttackScenario(BaseModel):
    """Complete attack scenario definition."""

    scenario_id: str
    name: str
    description: str
    total_nodes: int = Field(ge=3, le=20)
    node_configs: list[NodeAttackConfig]
    traffic_pattern: str
    scenario_duration_seconds: int
    defense_enabled: bool
    random_seed: int
    repetition_number: int


class ScenarioResult(BaseModel):
    """Result of a completed attack scenario."""

    scenario_id: str
    repetition_number: int
    random_seed: int
    started_at: int
    completed_at: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    detection_time_seconds: float | None = None
    false_positive_count: int
    nodes_quarantined: list[str]
    trust_events: list[str]