"""Work processing endpoint."""

import asyncio
import random

from fastapi import APIRouter
from pydantic import BaseModel

from services.node.config.settings import settings
from shared.utils.logger import get_logger

logger = get_logger("work")

router = APIRouter()


class WorkRequest(BaseModel):
    """Work request payload."""

    task: str = "process"
    data: str = ""


class WorkResponse(BaseModel):
    """Work response payload."""

    status: str
    node_id: str
    result: str


@router.post("/work")
async def process_work(request: WorkRequest) -> WorkResponse:
    """Process a work request.

    This simulates actual work with a small delay.
    """
    # Simulate work with random delay (50-150ms)
    delay = random.uniform(0.05, 0.15)
    await asyncio.sleep(delay)

    logger.info(
        "Work processed",
        node_id=settings.node_id,
        task=request.task,
        delay_ms=int(delay * 1000),
    )

    return WorkResponse(
        status="completed",
        node_id=settings.node_id,
        result=f"Processed {request.task} on {settings.node_id}",
    )