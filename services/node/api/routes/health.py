"""Health check endpoint."""

from fastapi import APIRouter

from services.node.config.settings import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "node",
        "node_id": settings.node_id,
    }