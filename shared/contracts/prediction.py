"""Prediction contracts for load-balancer-to-ML-service communication."""

from pydantic import BaseModel, Field


class MetricTimestep(BaseModel):
    """One time step of metrics for ML input."""

    timestamp: int
    cpu_percent: float
    memory_percent: float
    active_requests: int
    response_time_ms: float


class PredictionRequest(BaseModel):
    """Request from load balancer to ML service."""

    node_id: str
    recent_metrics: list[MetricTimestep] = Field(min_length=10, max_length=15)


class PredictionResponse(BaseModel):
    """Predicted load for the next 2 minutes."""

    node_id: str
    predicted_load: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
    predicted_at: int


class BatchPredictionRequest(BaseModel):
    """Batch prediction request for multiple nodes."""

    requests: list[PredictionRequest]


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""

    predictions: dict[str, PredictionResponse]