"""Load balancer FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.utils.logger import get_logger

logger = get_logger("load_balancer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("TrustScale Load Balancer starting...")
    yield
    logger.info("TrustScale Load Balancer shutting down...")


app = FastAPI(
    title="TrustScale Load Balancer",
    description="Byzantine-aware distributed load balancer",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "load_balancer"}