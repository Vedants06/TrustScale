"""Admin endpoints for load balancer configuration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.load_balancer.routing.router import get_active_strategy, set_active_strategy
from shared.utils.logger import get_logger

logger = get_logger("lb_admin")

router = APIRouter(prefix="/admin", tags=["admin"])


class SetStrategyRequest(BaseModel):
    strategy: str


@router.post("/set-strategy")
async def set_routing_strategy(request: SetStrategyRequest):
    valid_strategies = ["round_robin", "trust_aware"]

    if request.strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Valid options: {valid_strategies}",
        )

    set_active_strategy(request.strategy)
    logger.info("Routing strategy changed via admin", strategy=request.strategy)
    return {"status": "ok", "strategy": request.strategy}


@router.get("/strategy")
async def get_routing_strategy():
    return {"strategy": get_active_strategy()}