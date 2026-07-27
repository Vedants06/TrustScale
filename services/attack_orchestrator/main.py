"""Attack orchestrator FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from shared.utils.logger import get_logger

logger = get_logger("attack_orchestrator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    logger.info("TrustScale Attack Orchestrator starting...")
    yield
    logger.info("TrustScale Attack Orchestrator shutting down...")


app = FastAPI(
    title="TrustScale Attack Orchestrator",
    description="Byzantine attack scenario orchestration",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "attack_orchestrator"}