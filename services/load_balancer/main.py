"""Load balancer FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.load_balancer.api.middleware.metrics_middleware import MetricsMiddleware
from services.load_balancer.api.middleware.prometheus_middleware import PrometheusMiddleware
from services.load_balancer.api.routes import health, nodes, proxy
from services.load_balancer.config.settings import settings
from services.load_balancer.api.routes.admin import router as admin_router
from services.load_balancer.prediction.cache import cache_predictions
from services.load_balancer.prediction.client import fetch_predictions_for_nodes
from services.load_balancer.storage.redis_client import (
    close_redis_client,
    get_redis_client,
)
from shared.utils.logger import get_logger

logger = get_logger("load_balancer")

_prediction_refresh_task: asyncio.Task | None = None


async def refresh_predictions_loop() -> None:
    """Background task to periodically refresh ML predictions."""
    logger.info(
        "Prediction refresh loop started",
        interval_seconds=settings.prediction_refresh_interval_seconds,
    )

    while True:
        try:
            redis = await get_redis_client()
            node_ids = sorted(await redis.smembers("nodes:active"))

            if node_ids:
                predictions = await fetch_predictions_for_nodes(list(node_ids))
                await cache_predictions(predictions)
                logger.info(
                    "Predictions refreshed",
                    total_nodes=len(predictions),
                )
            else:
                logger.debug("No active nodes to predict for")

        except Exception as error:
            logger.error("Prediction refresh failed", error=str(error))

        await asyncio.sleep(settings.prediction_refresh_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    global _prediction_refresh_task

    logger.info("TrustScale Load Balancer starting...")
    await get_redis_client()
    _prediction_refresh_task = asyncio.create_task(refresh_predictions_loop())

    yield

    if _prediction_refresh_task is not None:
        _prediction_refresh_task.cancel()
        try:
            await _prediction_refresh_task
        except asyncio.CancelledError:
            pass

    await close_redis_client()
    logger.info("TrustScale Load Balancer shutting down...")


app = FastAPI(
    title="TrustScale Load Balancer",
    description="Byzantine-aware distributed load balancer",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(PrometheusMiddleware)
app.add_middleware(MetricsMiddleware)

app.include_router(health.router)
app.include_router(nodes.router)
app.include_router(proxy.router)
app.include_router(admin_router)