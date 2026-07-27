"""Health report sender to load balancer."""

import asyncio
import time

import aiohttp

from services.node.config.settings import settings
from services.node.crypto.signer import sign_health_report
from services.node.monitoring.metrics_collector import collect_metrics
from shared.contracts.health_report import HealthReport
from shared.utils.logger import get_logger

logger = get_logger("reporter")

_reporter_task: asyncio.Task | None = None


async def send_heartbeat() -> bool:
    """Send a signed health report to the load balancer.

    Returns:
        True if heartbeat was accepted, False otherwise.
    """
    # Collect metrics
    metrics = collect_metrics()

    # Create health report
    report = HealthReport(
        node_id=settings.node_id,
        timestamp=int(time.time()),
        metrics=metrics,
    )

    # Sign the report
    signed_report = sign_health_report(report)

    # Send to load balancer
    url = f"{settings.lb_url}/nodes/heartbeat"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=signed_report.model_dump(),
            ) as response:
                result = await response.json()

                if result.get("status") == "accepted":
                    logger.info("Heartbeat accepted", node_id=settings.node_id)
                    return True
                else:
                    logger.warning(
                        "Heartbeat rejected",
                        node_id=settings.node_id,
                        reason=result.get("reason"),
                    )
                    return False

    except Exception as e:
        logger.error("Failed to send heartbeat", error=str(e))
        return False


async def reporter_loop() -> None:
    """Background task that sends heartbeats periodically."""
    logger.info(
        "Reporter started",
        interval=settings.report_interval_seconds,
    )

    while True:
        await send_heartbeat()
        await asyncio.sleep(settings.report_interval_seconds)


async def start_reporter() -> None:
    """Start the background reporter task."""
    global _reporter_task
    _reporter_task = asyncio.create_task(reporter_loop())
    logger.info("Reporter task started")


async def stop_reporter() -> None:
    """Stop the background reporter task."""
    global _reporter_task
    if _reporter_task is not None:
        _reporter_task.cancel()
        try:
            await _reporter_task
        except asyncio.CancelledError:
            pass
        _reporter_task = None
        logger.info("Reporter task stopped")