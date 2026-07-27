"""Shared node information model."""

from pydantic import BaseModel, Field


class NodeInfo(BaseModel):
    """Information about a registered worker node."""

    node_id: str = Field(min_length=1)
    address: str
    port: int = Field(ge=1, le=65535)
    public_key: str