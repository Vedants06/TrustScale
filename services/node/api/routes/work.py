"""Work processing endpoint with real CPU computation."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter

import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel

from services.node.config.settings import settings
from services.node.monitoring.request_tracker import tracker
from shared.utils.logger import get_logger

logger = get_logger("work")

router = APIRouter()

# Dedicated thread pool for CPU work
# Prevents blocking the main event loop thread pool
_cpu_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cpu_work")


class WorkRequest(BaseModel):
    """Work request payload."""

    task: str = "process"
    data: str = ""
    intensity: int = 200


class WorkResponse(BaseModel):
    """Work response payload."""

    status: str
    node_id: str
    result: str


def cpu_intensive_work(matrix_size: int) -> str:
    """Perform real CPU work using matrix multiplication.

    Args:
        matrix_size: Size of square matrices to multiply (NxN).

    Returns:
        String summary of result.
    """
    A = np.random.rand(matrix_size, matrix_size).astype(np.float32)
    B = np.random.rand(matrix_size, matrix_size).astype(np.float32)
    C = np.dot(A, B)
    return f"{C[0][0]:.4f}"


@router.post("/work")
async def process_work(request: WorkRequest) -> WorkResponse:
    """Process a work request with real CPU computation."""
    await tracker.request_started()
    start = perf_counter()

    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            _cpu_executor,
            cpu_intensive_work,
            request.intensity,
        )

        duration_ms = (perf_counter() - start) * 1000

        logger.info(
            "Work processed",
            node_id=settings.node_id,
            task=request.task,
            duration_ms=round(duration_ms, 2),
            matrix_size=request.intensity,
        )

        return WorkResponse(
            status="completed",
            node_id=settings.node_id,
            result=f"Processed {request.task} on {settings.node_id}: {result}",
        )

    finally:
        duration_ms = (perf_counter() - start) * 1000
        await tracker.request_completed(duration_ms)