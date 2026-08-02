"""Health report sender to load balancer."""

import asyncio
import time

import aiohttp
import psutil

from services.node.config.settings import settings
from services.node.crypto.signer import sign_health_report
from services.node.monitoring.metrics_collector import collect_metrics
from shared.contracts.health_report import HealthReport
from shared.utils.logger import get_logger
from services.node.config.behavior_config import get_current_behavior

logger = get_logger("reporter")

_reporter_task: asyncio.Task | None = None


async def send_heartbeat() -> bool:
    """Send a signed health report to the load balancer."""
    try:
        real_metrics = collect_metrics()

        behavior = get_current_behavior()
        metrics = behavior.apply(real_metrics)

        report = HealthReport(
            node_id=settings.node_id,
            timestamp=int(time.time()),
            metrics=metrics,
        )

        signed_report = sign_health_report(report)

        url = f"{settings.lb_url}/nodes/heartbeat"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=signed_report.model_dump(),
            ) as response:
                result = await response.json()

                if result.get("status") == "accepted":
                    logger.info(
                        "Heartbeat accepted",
                        node_id=settings.node_id,
                        cpu=metrics.cpu_percent,
                        memory=metrics.memory_percent,
                        active_requests=metrics.active_requests,
                    )
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
    psutil.cpu_percent(interval=None)

    logger.info(
        "Reporter started",
        interval=settings.report_interval_seconds,
    )

    while True:
        try:
            await send_heartbeat()
        except Exception as e:
            logger.error("Reporter loop error", error=str(e))

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