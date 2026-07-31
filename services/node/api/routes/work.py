"""Work processing endpoint with request tracking."""

import asyncio
import random
from time import perf_counter

from fastapi import APIRouter
from pydantic import BaseModel

from services.node.config.settings import settings
from services.node.monitoring.request_tracker import tracker
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
    """Process a work request with real timing instrumentation."""
    await tracker.request_started()
    start = perf_counter()

    try:
        # Simulate work with random delay (50-150ms)
        delay = random.uniform(0.05, 0.15)
        await asyncio.sleep(delay)

        duration_ms = (perf_counter() - start) * 1000

        logger.info(
            "Work processed",
            node_id=settings.node_id,
            task=request.task,
            duration_ms=round(duration_ms, 2),
            active_requests=tracker.active_requests,
        )

        return WorkResponse(
            status="completed",
            node_id=settings.node_id,
            result=f"Processed {request.task} on {settings.node_id}",
        )

    finally:
        duration_ms = (perf_counter() - start) * 1000
        await tracker.request_completed(duration_ms)