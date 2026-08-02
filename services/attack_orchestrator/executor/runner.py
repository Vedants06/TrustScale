"""Execute attack scenarios end-to-end."""

import asyncio
import time

import httpx

from services.attack_orchestrator.executor.metrics_collector import (
    ScenarioMetrics,
    get_node_trust_score,
    send_work_request,
)
from services.attack_orchestrator.scenarios.base import ScenarioConfig
from shared.utils.logger import get_logger

logger = get_logger("scenario_runner")

LB_URL = "http://load_balancer:8000"
NODE_BASE_URL = "http://{node_id}:8001"


async def set_node_behavior(
    node_id: str,
    mode: str,
    intensity: float,
) -> bool:
    """Change a node's behavior via admin API.

    Args:
        node_id: Node identifier.
        mode: Behavior mode (honest, under_reporter, over_reporter).
        intensity: Behavior intensity (0.0 to 1.0).

    Returns:
        True if behavior was set successfully.
    """
    url = f"http://{node_id}:8001/admin/set-behavior"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"mode": mode, "intensity": intensity},
                timeout=5.0,
            )

        if response.status_code == 200:
            logger.info(
                "Node behavior set",
                node_id=node_id,
                mode=mode,
                intensity=intensity,
            )
            return True
        else:
            logger.warning(
                "Failed to set node behavior",
                node_id=node_id,
                status=response.status_code,
            )
            return False

    except Exception as error:
        logger.error(
            "Error setting node behavior",
            node_id=node_id,
            error=str(error),
        )
        return False


async def reset_all_nodes_to_honest(node_ids: list[str]) -> None:
    """Reset all nodes back to honest behavior."""
    tasks = [
        set_node_behavior(node_id, "honest", 0.0)
        for node_id in node_ids
    ]
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("All nodes reset to honest behavior")


async def collect_initial_trust_scores(
    node_ids: list[str],
    metrics: ScenarioMetrics,
) -> None:
    """Snapshot trust scores before the attack begins."""
    for node_id in node_ids:
        score = await get_node_trust_score(node_id)
        if score is not None:
            metrics.initial_trust_scores[node_id] = score


async def collect_final_trust_scores(
    node_ids: list[str],
    metrics: ScenarioMetrics,
) -> None:
    """Snapshot trust scores after the scenario ends."""
    for node_id in node_ids:
        score = await get_node_trust_score(node_id)
        if score is not None:
            metrics.final_trust_scores[score] = score
            metrics.final_trust_scores[node_id] = score


async def monitor_for_quarantine(
    target_node_ids: list[str],
    metrics: ScenarioMetrics,
    poll_interval: float = 2.0,
    max_duration: float = 180.0,
) -> None:
    """Poll trust scores and record when target nodes get quarantined.

    Args:
        target_node_ids: Nodes we expect to be quarantined.
        metrics: Metrics object to update.
        poll_interval: Seconds between polls.
        max_duration: Maximum time to monitor.
    """
    start = time.time()

    while time.time() - start < max_duration:
        for node_id in target_node_ids:
            if node_id in metrics.nodes_quarantined:
                continue

            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{LB_URL}/nodes/{node_id}/trust",
                        timeout=5.0,
                    )

                if response.status_code == 200:
                    data = response.json()
                    quarantine = data.get("quarantine", {})

                    if quarantine.get("is_quarantined"):
                        elapsed = time.time() - metrics.started_at
                        metrics.nodes_quarantined.append(node_id)

                        if metrics.detection_time_seconds is None:
                            metrics.detection_time_seconds = round(elapsed, 2)

                        logger.info(
                            "Node quarantined during scenario",
                            node_id=node_id,
                            detection_time=metrics.detection_time_seconds,
                        )

            except Exception:
                pass

        if len(metrics.nodes_quarantined) == len(target_node_ids):
            logger.info(
                "All target nodes quarantined",
                count=len(metrics.nodes_quarantined),
            )
            break

        await asyncio.sleep(poll_interval)


async def run_scenario(
    config: ScenarioConfig,
    repetition_number: int = 1,
) -> ScenarioMetrics:
    """Execute a complete attack scenario.

    Args:
        config: Scenario configuration.
        repetition_number: Which repetition this is (1-5).

    Returns:
        Metrics collected during the scenario.
    """
    logger.info(
        "Starting scenario",
        scenario_id=config.scenario_id,
        repetition=repetition_number,
        seed=config.random_seed,
    )

    all_node_ids = [f"node_{i}" for i in range(1, config.total_nodes + 1)]
    target_node_ids = [n.node_id for n in config.target_nodes]

    metrics = ScenarioMetrics(
        scenario_id=config.scenario_id,
        repetition_number=repetition_number,
        random_seed=config.random_seed,
    )

    try:
        # Step 1: Reset all nodes to honest baseline
        await reset_all_nodes_to_honest(all_node_ids)
        await asyncio.sleep(5)

        # Step 2: Collect initial trust scores
        await collect_initial_trust_scores(all_node_ids, metrics)

        logger.info(
            "Initial trust scores",
            scores=metrics.initial_trust_scores,
        )

        # Step 3: Start background monitoring for quarantine
        monitor_task = asyncio.create_task(
            monitor_for_quarantine(
                target_node_ids=target_node_ids,
                metrics=metrics,
                max_duration=float(config.scenario_duration_seconds),
            )
        )

        # Step 4: Run scenario phases
        scenario_start = time.time()

        for node_config in config.target_nodes:
            # Wait until this node's start time
            while (time.time() - scenario_start) < node_config.start_at_seconds:
                await asyncio.sleep(0.5)

            # Activate attack behavior
            await set_node_behavior(
                node_id=node_config.node_id,
                mode=node_config.behavior,
                intensity=node_config.intensity,
            )

        # Step 5: Generate traffic during scenario
        traffic_end = scenario_start + config.scenario_duration_seconds
        request_interval = 1.0

        while time.time() < traffic_end:
            await send_work_request(metrics)
            await asyncio.sleep(request_interval)

        # Step 6: Wait for monitoring to complete
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

        # Step 7: Collect final trust scores
        await collect_final_trust_scores(all_node_ids, metrics)

        # Step 8: Reset all nodes to honest
        await reset_all_nodes_to_honest(all_node_ids)

        metrics.completed_at = time.time()

        logger.info(
            "Scenario complete",
            scenario_id=config.scenario_id,
            repetition=repetition_number,
            total_requests=metrics.total_requests,
            success_rate=round(metrics.success_rate, 4),
            detection_time=metrics.detection_time_seconds,
            nodes_quarantined=metrics.nodes_quarantined,
        )

    except Exception as error:
        logger.error(
            "Scenario failed",
            scenario_id=config.scenario_id,
            error=str(error),
        )
        metrics.completed_at = time.time()
        await reset_all_nodes_to_honest(all_node_ids)

    return metrics