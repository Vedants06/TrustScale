from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import structlog

from services.node.config.behavior_config import (
    BEHAVIOR_REGISTRY,
    set_current_behavior,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])


class SetBehaviorRequest(BaseModel):
    mode: str = Field(..., description="honest | under_reporter | over_reporter")
    intensity: float = Field(default=0.5, ge=0.0, le=1.0)


@router.post("/set-behavior")
async def set_behavior(payload: SetBehaviorRequest):
    if payload.mode not in BEHAVIOR_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown behavior mode: {payload.mode}. "
                   f"Valid options: {list(BEHAVIOR_REGISTRY.keys())}",
        )
    set_current_behavior(payload.mode, payload.intensity)
    return {"status": "ok", "mode": payload.mode}