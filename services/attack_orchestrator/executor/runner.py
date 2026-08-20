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


async def set_node_behavior(
    node_id: str,
    mode: str,
    intensity: float,
) -> bool:
    """Change a node's behavior via admin API (supports remote nodes across LAN)."""
    # Dynamic address lookup from LB registry
    node_address = node_id
    node_port = 8001

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{LB_URL}/nodes/{node_id}/info", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                node_address = data.get("address", node_id)
                node_port = data.get("port", 8001)
    except Exception:
        pass

    url = f"http://{node_address}:{node_port}/admin/set-behavior"

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
                address=node_address,
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
            metrics.final_trust_scores[node_id] = score


async def monitor_for_quarantine(
    target_node_ids: list[str],
    metrics: ScenarioMetrics,
    poll_interval: float = 2.0,
    max_duration: float = 300.0,
) -> None:
    """Poll trust scores and record when target nodes get quarantined."""
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


async def set_lb_routing_strategy(strategy: str) -> bool:
    """Switch the LB routing strategy for the scenario."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{LB_URL}/admin/set-strategy",
                json={"strategy": strategy},
                timeout=5.0,
            )
        if response.status_code == 200:
            logger.info("LB routing strategy set", strategy=strategy)
            return True
        logger.warning(
            "Failed to set routing strategy",
            status=response.status_code,
        )
        return False
    except Exception as error:
        logger.warning("Failed to set routing strategy", error=str(error))
        return False


async def run_scenario(
    config: ScenarioConfig,
    repetition_number: int = 1,
) -> ScenarioMetrics:
    """Execute a complete attack scenario."""
    logger.info(
        "Starting scenario",
        scenario_id=config.scenario_id,
        repetition=repetition_number,
        seed=config.random_seed,
        defense_enabled=config.defense_enabled,
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

        # Step 2: Switch to round_robin so all nodes receive traffic
        # This ensures cross-validation has observations for all nodes
        logger.info("Switching to round_robin for scenario observation")
        await set_lb_routing_strategy("round_robin")
        await asyncio.sleep(2)

        # Step 3: Collect initial trust scores
        await collect_initial_trust_scores(all_node_ids, metrics)

        logger.info(
            "Initial trust scores",
            scores=metrics.initial_trust_scores,
        )

        # Step 4: If defense disabled, freeze trust scores
        if not config.defense_enabled:
            logger.info("Defense disabled — freezing trust scores")
            await _freeze_trust_scores(all_node_ids, value=1.0)

        # Step 5: Start background quarantine monitoring
        monitor_task = None
        if config.defense_enabled:
            monitor_task = asyncio.create_task(
                monitor_for_quarantine(
                    target_node_ids=target_node_ids,
                    metrics=metrics,
                    max_duration=float(config.scenario_duration_seconds),
                )
            )

        # Step 6: Run scenario phases
        scenario_start = time.time()

        for node_config in config.target_nodes:
            while (time.time() - scenario_start) < node_config.start_at_seconds:
                await asyncio.sleep(0.5)

            await set_node_behavior(
                node_id=node_config.node_id,
                mode=node_config.behavior,
                intensity=node_config.intensity,
            )

        # Step 7: Generate traffic during scenario
        traffic_end = scenario_start + config.scenario_duration_seconds
        request_interval = 0.5

        while time.time() < traffic_end:
            await send_work_request(metrics)
            await asyncio.sleep(request_interval)

        # Step 8: Cancel monitoring
        if monitor_task is not None:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass

        # Step 9: Collect final trust scores
        await collect_final_trust_scores(all_node_ids, metrics)

        # Step 10: Reset everything
        await reset_all_nodes_to_honest(all_node_ids)

        # Step 11: Restore trust_aware routing
        logger.info("Restoring trust_aware routing after scenario")
        await set_lb_routing_strategy("trust_aware")

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
        # Always restore routing on error
        await set_lb_routing_strategy("trust_aware")

    return metrics


async def _freeze_trust_scores(
    node_ids: list[str],
    value: float = 1.0,
) -> None:
    """Temporarily set all trust scores to a fixed value."""
    import redis.asyncio as redis_lib

    client = redis_lib.from_url(
        "redis://redis:6379",
        encoding="utf-8",
        decode_responses=True,
    )

    for node_id in node_ids:
        await client.set(f"trust:{node_id}", str(value))

    await client.aclose()

    logger.info(
        "Trust scores frozen for no-defense baseline",
        node_ids=node_ids,
        value=value,
    )