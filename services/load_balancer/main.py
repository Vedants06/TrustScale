"""Load balancer FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.load_balancer.api.middleware.metrics_middleware import MetricsMiddleware
from services.load_balancer.api.routes import health, nodes, proxy
from services.load_balancer.storage.redis_client import (
    close_redis_client,
    get_redis_client,
)
from shared.utils.logger import get_logger

logger = get_logger("load_balancer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("TrustScale Load Balancer starting...")

    await get_redis_client()

    yield

    await close_redis_client()
    logger.info("TrustScale Load Balancer shutting down...")


app = FastAPI(
    title="TrustScale Load Balancer",
    description="Byzantine-aware distributed load balancer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(MetricsMiddleware)

app.include_router(health.router)
app.include_router(nodes.router)
app.include_router(proxy.router)