"""Shared metric snapshot model."""

from pydantic import BaseModel, Field


class MetricSnapshot(BaseModel):
    """A timestamped snapshot of node metrics."""

    timestamp: int
    node_id: str
    cpu_percent: float = Field(ge=0.0, le=100.0)
    memory_percent: float = Field(ge=0.0, le=100.0)
    active_requests: int = Field(ge=0)
    response_time_ms: float = Field(ge=0.0)