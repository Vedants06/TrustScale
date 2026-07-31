"""Save and load trained ML models."""

import os
from pathlib import Path

import torch

from shared.utils.logger import get_logger

logger = get_logger("model_registry")

MODEL_DIR = Path(os.getenv("MODEL_DIR", "research/data/models"))


def save_model(model: torch.nn.Module, version: str) -> Path:
    """Save a trained model to disk.

    Args:
        model: Trained PyTorch model.
        version: Model version string.

    Returns:
        Path where model was saved.
    """
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = MODEL_DIR / f"lstm_{version}.pt"
    torch.save(model.state_dict(), path)
    logger.info("Model saved", path=str(path), version=version)
    return path


def load_model(
    model: torch.nn.Module,
    version: str,
) -> torch.nn.Module:
    """Load a saved model from disk.

    Args:
        model: Model instance with correct architecture.
        version: Model version string to load.

    Returns:
        Model with loaded weights.
    """
    path = MODEL_DIR / f"lstm_{version}.pt"

    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    model.load_state_dict(torch.load(path, weights_only=True))
    model.eval()
    logger.info("Model loaded", path=str(path), version=version)
    return model


def get_latest_model_version() -> str | None:
    """Get the latest available model version.

    Returns:
        Version string or None if no models exist.
    """
    if not MODEL_DIR.exists():
        return None

    model_files = sorted(MODEL_DIR.glob("lstm_*.pt"))
    if not model_files:
        return None

    latest = model_files[-1]
    version = latest.stem.replace("lstm_", "")
    return version