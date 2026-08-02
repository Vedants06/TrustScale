"""Worker node FastAPI application entry point."""

from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from services.node.api.routes import health, work, metrics, admin
from services.node.config.settings import settings
from services.node.crypto.keypair import initialize_keypair, get_public_key_pem
from services.node.config.behavior_config import load_behavior_from_env
from services.node.monitoring.reporter import start_reporter, stop_reporter
from shared.utils.logger import get_logger

logger = get_logger("node")


async def register_with_lb() -> bool:
    """Register this node with the load balancer."""
    url = f"{settings.lb_url}/nodes/register"

    payload = {
        "node_id": settings.node_id,
        "address": settings.node_id,
        "port": settings.node_port,
        "public_key": get_public_key_pem(),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()

                if result.get("status") == "registered":
                    logger.info(
                        "Registered with load balancer",
                        node_id=settings.node_id,
                    )
                    return True
                else:
                    logger.error("Registration failed", result=result)
                    return False

    except Exception as e:
        logger.error("Failed to register with load balancer", error=str(e))
        return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info(f"Node {settings.node_id} starting...")

    initialize_keypair()
   
    behavior = load_behavior_from_env()
    logger.info(
        "Behavior mode active",
        node_id=settings.node_id,
        mode=behavior.name,
        intensity=behavior.intensity,
    )
    # Warm up numpy BLAS on startup to avoid cold start delay
    logger.info("Warming up numpy BLAS...")
    import numpy as np
    A = np.random.rand(10, 10).astype(np.float32)
    B = np.random.rand(10, 10).astype(np.float32)
    _ = np.dot(A, B)
    logger.info("Numpy BLAS warmed up")

    await register_with_lb()
    await start_reporter()

    yield

    await stop_reporter()
    logger.info(f"Node {settings.node_id} shutting down...")


app = FastAPI(
    title=f"TrustScale Node {settings.node_id}",
    description="Worker node for TrustScale cluster",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(work.router)
app.include_router(metrics.router)
app.include_router(admin.router)