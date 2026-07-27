"""Worker node FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from services.node.config.settings import settings
from shared.utils.logger import get_logger

logger = get_logger("node")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info(f"Node {settings.node_id} starting...", node_id=settings.node_id)
    yield
    logger.info(f"Node {settings.node_id} shutting down...", node_id=settings.node_id)


app = FastAPI(
    title=f"TrustScale Node {settings.node_id}",
    description="Worker node for TrustScale cluster",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "node", "node_id": settings.node_id}