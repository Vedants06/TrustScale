"""Base attack scenario definition."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NodeAttackConfig:
    """Attack configuration for a single node."""

    node_id: str
    behavior: str
    intensity: float
    start_at_seconds: int
    duration_seconds: int


@dataclass
class ScenarioConfig:
    """Complete attack scenario configuration."""

    scenario_id: str
    name: str
    description: str
    total_nodes: int
    target_nodes: list[NodeAttackConfig]
    traffic_pattern: str
    scenario_duration_seconds: int
    defense_enabled: bool
    random_seed: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScenarioConfig":
        """Build ScenarioConfig from a YAML-parsed dictionary."""
        target_nodes = [
            NodeAttackConfig(
                node_id=n["node_id"],
                behavior=n["behavior"],
                intensity=n["intensity"],
                start_at_seconds=n["start_at_seconds"],
                duration_seconds=n["duration_seconds"],
            )
            for n in data.get("target_nodes", [])
        ]

        return cls(
            scenario_id=data["scenario_id"],
            name=data["name"],
            description=data.get("description", ""),
            total_nodes=data["total_nodes"],
            target_nodes=target_nodes,
            traffic_pattern=data.get("traffic_pattern", "steady_state"),
            scenario_duration_seconds=data["scenario_duration_seconds"],
            defense_enabled=data.get("defense_enabled", True),
            random_seed=data.get("random_seed", 42),
        )