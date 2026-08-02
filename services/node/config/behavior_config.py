import os
import structlog

from services.node.behavior.base import BaseBehavior
from services.node.behavior.honest import HonestBehavior
from services.node.behavior.under_reporter import UnderReporterBehavior
from services.node.behavior.over_reporter import OverReporterBehavior

logger = structlog.get_logger()

BEHAVIOR_REGISTRY = {
    "honest": HonestBehavior,
    "under_reporter": UnderReporterBehavior,
    "over_reporter": OverReporterBehavior,
}

_current_behavior: BaseBehavior = HonestBehavior(intensity=0.0)


def build_behavior(mode: str, intensity: float) -> BaseBehavior:
    behavior_cls = BEHAVIOR_REGISTRY.get(mode)
    if behavior_cls is None:
        raise ValueError(f"Unknown behavior mode: {mode}")
    return behavior_cls(intensity=intensity)


def load_behavior_from_env() -> BaseBehavior:
    """Called once on node startup."""
    global _current_behavior
    mode = os.getenv("BEHAVIOR_MODE", "honest")
    intensity = float(os.getenv("BEHAVIOR_INTENSITY", "0.5"))
    _current_behavior = build_behavior(mode, intensity)
    logger.info("behavior_loaded", mode=mode, intensity=intensity)
    return _current_behavior


def get_current_behavior() -> BaseBehavior:
    return _current_behavior


def set_current_behavior(mode: str, intensity: float) -> BaseBehavior:
    """Called by the admin endpoint to switch behavior at runtime."""
    global _current_behavior
    _current_behavior = build_behavior(mode, intensity)
    logger.info("behavior_changed", mode=mode, intensity=intensity)
    return _current_behavior