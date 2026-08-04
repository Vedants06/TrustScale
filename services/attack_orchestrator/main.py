"""Attack orchestrator FastAPI application."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

import yaml
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from services.attack_orchestrator.evaluator.report_generator import (
    append_to_csv_summary,
    save_scenario_result,
)
from services.attack_orchestrator.executor.runner import run_scenario
from services.attack_orchestrator.scenarios.base import ScenarioConfig
from shared.utils.logger import get_logger

logger = get_logger("attack_orchestrator")

SCENARIOS_DIR = Path(
    os.getenv("SCENARIOS_DIR", "config/attack_scenarios")
)

_loaded_scenarios: dict[str, ScenarioConfig] = {}
_running_scenario: str | None = None


def load_all_scenarios() -> dict[str, ScenarioConfig]:
    """Load all YAML scenario files from the scenarios directory."""
    scenarios: dict[str, ScenarioConfig] = {}

    if not SCENARIOS_DIR.exists():
        logger.warning("Scenarios directory not found", path=str(SCENARIOS_DIR))
        return scenarios

    for yaml_file in SCENARIOS_DIR.glob("*.yml"):
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            config = ScenarioConfig.from_dict(data)
            scenarios[config.scenario_id] = config

            logger.info(
                "Scenario loaded",
                scenario_id=config.scenario_id,
                name=config.name,
            )

        except Exception as error:
            logger.error(
                "Failed to load scenario",
                file=str(yaml_file),
                error=str(error),
            )

    return scenarios


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load scenarios on startup."""
    global _loaded_scenarios

    logger.info("TrustScale Attack Orchestrator starting...")
    _loaded_scenarios = load_all_scenarios()

    logger.info(
        "Attack Orchestrator ready",
        scenarios_loaded=len(_loaded_scenarios),
        scenario_ids=list(_loaded_scenarios.keys()),
    )

    yield

    logger.info("Attack Orchestrator shutting down...")


app = FastAPI(
    title="TrustScale Attack Orchestrator",
    description="Byzantine attack scenario orchestration",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


router = APIRouter()


class RunScenarioRequest(BaseModel):
    """Request to run a scenario."""

    scenario_id: str
    repetition_number: int = 1


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "attack_orchestrator",
        "scenarios_loaded": len(_loaded_scenarios),
    }


@router.get("/scenarios")
async def list_scenarios():
    """List all available scenarios."""
    return {
        "scenarios": [
            {
                "scenario_id": config.scenario_id,
                "name": config.name,
                "description": config.description,
                "total_nodes": config.total_nodes,
                "target_nodes": len(config.target_nodes),
                "duration_seconds": config.scenario_duration_seconds,
                "defense_enabled": config.defense_enabled,
            }
            for config in _loaded_scenarios.values()
        ]
    }


@router.get("/scenarios/status")
async def get_running_status():
    """Get currently running scenario status."""
    return {
        "running_scenario": _running_scenario,
        "is_running": _running_scenario is not None,
    }


@router.get("/scenarios/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get details of a specific scenario."""
    if scenario_id not in _loaded_scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {scenario_id}",
        )

    config = _loaded_scenarios[scenario_id]
    return {
        "scenario_id": config.scenario_id,
        "name": config.name,
        "description": config.description,
        "total_nodes": config.total_nodes,
        "target_nodes": [
            {
                "node_id": n.node_id,
                "behavior": n.behavior,
                "intensity": n.intensity,
                "start_at_seconds": n.start_at_seconds,
                "duration_seconds": n.duration_seconds,
            }
            for n in config.target_nodes
        ],
        "scenario_duration_seconds": config.scenario_duration_seconds,
        "defense_enabled": config.defense_enabled,
        "random_seed": config.random_seed,
    }


async def _run_and_save(
    config: ScenarioConfig,
    repetition_number: int,
) -> None:
    """Background task to run scenario and save results."""
    global _running_scenario

    _running_scenario = config.scenario_id

    try:
        metrics = await run_scenario(
            config=config,
            repetition_number=repetition_number,
        )

        save_scenario_result(metrics)
        append_to_csv_summary(metrics)

        logger.info(
            "Scenario completed and saved",
            scenario_id=config.scenario_id,
            repetition=repetition_number,
            success_rate=round(metrics.success_rate, 4),
            detection_time=metrics.detection_time_seconds,
        )

    except Exception as error:
        logger.error(
            "Scenario execution failed",
            scenario_id=config.scenario_id,
            error=str(error),
        )
    finally:
        _running_scenario = None


@router.post("/scenarios/run")
async def run_scenario_endpoint(
    request: RunScenarioRequest,
    background_tasks: BackgroundTasks,
):
    """Trigger a scenario to run in the background."""
    global _running_scenario

    if _running_scenario is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Scenario already running: {_running_scenario}",
        )

    if request.scenario_id not in _loaded_scenarios:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario not found: {request.scenario_id}",
        )

    config = _loaded_scenarios[request.scenario_id]

    background_tasks.add_task(
        _run_and_save,
        config=config,
        repetition_number=request.repetition_number,
    )

    logger.info(
        "Scenario triggered",
        scenario_id=request.scenario_id,
        repetition=request.repetition_number,
    )

    return {
        "status": "started",
        "scenario_id": request.scenario_id,
        "repetition_number": request.repetition_number,
        "message": "Scenario running in background",
    }


@router.get("/experiments")
async def list_experiments():
    """List all past scenario runs from research/data/experiments/."""
    experiments_dir = Path("research/data/experiments")

    if not experiments_dir.exists():
        return {"experiments": []}

    experiments = []
    for scenario_dir in experiments_dir.iterdir():
        if not scenario_dir.is_dir():
            continue

        scenario_id = scenario_dir.name
        result_files = sorted(scenario_dir.glob("rep*.json"))

        for result_file in result_files:
            try:
                with open(result_file) as f:
                    import json as json_lib
                    data = json_lib.load(f)

                experiments.append({
                    "scenario_id": scenario_id,
                    "file_name": result_file.name,
                    "repetition_number": data.get("repetition_number"),
                    "started_at": data.get("started_at"),
                    "detection_time_seconds": data.get("detection_time_seconds"),
                    "success_rate": data.get("success_rate"),
                    "nodes_quarantined": data.get("nodes_quarantined", []),
                })
            except Exception:
                continue

    experiments.sort(
        key=lambda x: x.get("started_at", 0),
        reverse=True,
    )

    return {"experiments": experiments}


@router.get("/experiments/{scenario_id}/{file_name}")
async def get_experiment(scenario_id: str, file_name: str):
    """Get details of a specific past scenario run."""
    file_path = Path("research/data/experiments") / scenario_id / file_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Experiment not found")

    with open(file_path) as f:
        import json as json_lib
        data = json_lib.load(f)

    return data


app.include_router(router)