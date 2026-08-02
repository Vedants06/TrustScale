"""Generate scenario result files."""

import csv
import json
import time
from pathlib import Path

from services.attack_orchestrator.executor.metrics_collector import ScenarioMetrics
from shared.utils.logger import get_logger

logger = get_logger("report_generator")

EXPERIMENTS_DIR = Path("research/data/experiments")


def ensure_experiment_dir(scenario_id: str) -> Path:
    """Create experiment directory for a scenario."""
    scenario_dir = EXPERIMENTS_DIR / scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)
    return scenario_dir


def save_scenario_result(metrics: ScenarioMetrics) -> Path:
    """Save scenario result to JSON file.

    Args:
        metrics: Completed scenario metrics.

    Returns:
        Path to the saved result file.
    """
    scenario_dir = ensure_experiment_dir(metrics.scenario_id)

    filename = (
        f"rep{metrics.repetition_number:02d}"
        f"_seed{metrics.random_seed}"
        f"_{int(metrics.started_at)}.json"
    )

    result_path = scenario_dir / filename
    result_data = metrics.to_dict()

    with open(result_path, "w") as f:
        json.dump(result_data, f, indent=2)

    logger.info(
        "Result saved",
        path=str(result_path),
        scenario_id=metrics.scenario_id,
    )

    return result_path


def append_to_csv_summary(metrics: ScenarioMetrics) -> Path:
    """Append scenario result to a CSV summary file.

    Args:
        metrics: Completed scenario metrics.

    Returns:
        Path to the CSV file.
    """
    scenario_dir = ensure_experiment_dir(metrics.scenario_id)
    csv_path = scenario_dir / "results_summary.csv"

    result_dict = metrics.to_dict()

    fieldnames = [
        "scenario_id",
        "repetition_number",
        "random_seed",
        "started_at",
        "duration_seconds",
        "total_requests",
        "successful_requests",
        "failed_requests",
        "success_rate",
        "avg_latency_ms",
        "p95_latency_ms",
        "detection_time_seconds",
        "nodes_quarantined",
    ]

    file_exists = csv_path.exists()

    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        row = {k: result_dict.get(k, "") for k in fieldnames}
        row["nodes_quarantined"] = str(result_dict.get("nodes_quarantined", []))
        writer.writerow(row)

    logger.info(
        "CSV summary updated",
        path=str(csv_path),
        scenario_id=metrics.scenario_id,
    )

    return csv_path