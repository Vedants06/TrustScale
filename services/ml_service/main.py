"""ML service FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.ml_service.api.routes import health, predict, metrics
from shared.utils.logger import get_logger

logger = get_logger("ml_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("TrustScale ML Service starting...")
    yield
    logger.info("TrustScale ML Service shutting down...")


app = FastAPI(
    title="TrustScale ML Service",
    description="Load prediction service for TrustScale",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(predict.router)
app.include_router(metrics.router)