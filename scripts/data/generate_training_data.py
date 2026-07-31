"""Generate synthetic training data as fallback if Prometheus data is insufficient.

Run from project root:
    python scripts/data/generate_training_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import numpy as np
import pandas as pd

from services.ml_service.training.feature_engineering import add_composite_load_column
from shared.utils.logger import get_logger

logger = get_logger("generate_training_data")

OUTPUT_DIR = Path("research/data/training")
RANDOM_SEED = 42
TOTAL_TIMESTEPS = 2000
NODE_IDS = ["node_1", "node_2", "node_3"]


def generate_realistic_load_pattern(
    n_timesteps: int,
    base_load: float = 0.3,
    noise_scale: float = 0.05,
    spike_probability: float = 0.05,
    seed: int = 42,
) -> np.ndarray:
    """Generate realistic load pattern with noise and occasional spikes.

    Args:
        n_timesteps: Number of timesteps to generate.
        base_load: Base load level (0-1).
        noise_scale: Standard deviation of noise.
        spike_probability: Probability of a load spike at each step.
        seed: Random seed for reproducibility.

    Returns:
        Array of load values between 0 and 1.
    """
    rng = np.random.default_rng(seed)

    load = np.zeros(n_timesteps)
    current_load = base_load

    for i in range(n_timesteps):
        noise = rng.normal(0, noise_scale)

        if rng.random() < spike_probability:
            spike = rng.uniform(0.2, 0.5)
            current_load = min(1.0, current_load + spike)
        else:
            current_load = max(0.0, min(1.0, current_load + noise))
            current_load = current_load * 0.95 + base_load * 0.05

        load[i] = current_load

    return load


def main() -> None:
    """Generate synthetic training data for all nodes."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows = []

    for i, node_id in enumerate(NODE_IDS):
        load_pattern = generate_realistic_load_pattern(
            n_timesteps=TOTAL_TIMESTEPS,
            base_load=0.2 + i * 0.1,
            noise_scale=0.03,
            spike_probability=0.05,
            seed=RANDOM_SEED + i,
        )

        for t, load in enumerate(load_pattern):
            cpu_percent = load * 100.0
            active_requests = load * 50.0
            response_time_ms = 50.0 + load * 950.0

            all_rows.append({
                "node_id": node_id,
                "timestamp": t * 5,
                "cpu_percent": round(cpu_percent, 2),
                "memory_percent": round(30.0 + load * 40.0, 2),
                "active_requests": round(active_requests, 1),
                "response_time_ms": round(response_time_ms, 2),
            })

    df = pd.DataFrame(all_rows)
    df = add_composite_load_column(df)

    output_path = OUTPUT_DIR / "baseline_metrics.csv"
    df.to_csv(output_path, index=False)

    logger.info(
        "Synthetic training data generated",
        rows=len(df),
        nodes=NODE_IDS,
        output_path=str(output_path),
    )

    print(f"\nGenerated {len(df)} rows of synthetic training data")
    print(f"Saved to: {output_path}")
    print(f"Composite load range: {df['composite_load'].min():.3f} - {df['composite_load'].max():.3f}")


if __name__ == "__main__":
    main()