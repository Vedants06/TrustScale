"""Health report contracts for node-to-load-balancer communication."""

from pydantic import BaseModel, Field


class NodeMetrics(BaseModel):
    """Metrics reported by a node about itself."""

    cpu_percent: float = Field(ge=0.0, le=100.0)
    memory_percent: float = Field(ge=0.0, le=100.0)
    active_requests: int = Field(ge=0)
    total_requests_last_5s: int = Field(ge=0)
    avg_response_time_ms: float = Field(ge=0.0)
    uptime_seconds: int = Field(ge=0)


class HealthReport(BaseModel):
    """Unsigned health report data."""

    node_id: str = Field(min_length=1)
    timestamp: int
    metrics: NodeMetrics
    version: str = Field(default="1.0")


class SignedHealthReport(BaseModel):
    """Health report with cryptographic signature."""

    report: HealthReport
    signature: str
    public_key_id: str