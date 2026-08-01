"""Train the LSTM load prediction model on real cluster data.

Run from project root:
    python scripts/ml/train_model.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ml_service.config.model_config import (
    BATCH_SIZE,
    EARLY_STOPPING_PATIENCE,
    LEARNING_RATE,
    LSTM_DROPOUT,
    LSTM_HIDDEN_SIZE,
    LSTM_INPUT_SIZE,
    LSTM_NUM_LAYERS,
    SEQUENCE_LENGTH,
    TRAIN_SPLIT,
    TRAINING_EPOCHS,
)
from services.ml_service.models.lstm_model import LSTMLoadPredictor
from services.ml_service.storage.metrics_fetcher import fetch_all_nodes_training_data
from services.ml_service.storage.model_registry import save_model
from services.ml_service.training.data_loader import create_data_loaders
from services.ml_service.training.evaluator import evaluate_model
from services.ml_service.training.feature_engineering import (
    add_composite_load_column,
    prepare_training_data,
)
from services.ml_service.training.trainer import train_model
from shared.utils.logger import get_logger

import pandas as pd

logger = get_logger("train_model_script")


def main() -> None:
    """Run the full training pipeline."""
    logger.info("Starting LSTM training pipeline")

    # Step 1: Fetch training data from Prometheus
    logger.info("Fetching training data from Prometheus...")
    all_node_data = fetch_all_nodes_training_data(duration_minutes=60)

    if not all_node_data:
        logger.error(
            "No training data available from Prometheus. "
            "Make sure the cluster has been running and generating traffic."
        )
        sys.exit(1)

    # Step 2: Combine all node data
    all_dfs = []
    for node_id, df in all_node_data.items():
        df = df.copy()
        df["node_id"] = node_id
        all_dfs.append(df)

    combined_df = pd.concat(all_dfs, ignore_index=True)
    combined_df = add_composite_load_column(combined_df)

    logger.info(
        "Training data combined",
        total_rows=len(combined_df),
        nodes=list(all_node_data.keys()),
    )

    # Step 3: Check minimum data requirement
    if len(combined_df) < SEQUENCE_LENGTH + 10:
        logger.error(
            "Not enough training data.",
            rows=len(combined_df),
            required=SEQUENCE_LENGTH + 10,
        )
        sys.exit(1)

    # Step 4: Prepare sequences
    try:
        X_train, y_train, X_val, y_val = prepare_training_data(
            df=combined_df,
            sequence_length=SEQUENCE_LENGTH,
            train_split=TRAIN_SPLIT,
        )
    except ValueError as error:
        logger.error("Failed to prepare training data", error=str(error))
        sys.exit(1)

    # Step 5: Create data loaders
    train_loader, val_loader = create_data_loaders(
        X_train=X_train,
        y_train=y_train,
        X_val=X_val,
        y_val=y_val,
        batch_size=BATCH_SIZE,
    )

    # Step 6: Initialize model
    model = LSTMLoadPredictor(
        input_size=LSTM_INPUT_SIZE,
        hidden_size=LSTM_HIDDEN_SIZE,
        num_layers=LSTM_NUM_LAYERS,
        dropout=LSTM_DROPOUT,
    )

    logger.info("LSTM model initialized", architecture=str(model))

    # Step 7: Train model
    history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=TRAINING_EPOCHS,
        learning_rate=LEARNING_RATE,
        patience=EARLY_STOPPING_PATIENCE,
    )

    # Step 8: Evaluate model
    eval_metrics = evaluate_model(model, val_loader)

    logger.info(
        "Training complete",
        mae=eval_metrics["mae"],
        rmse=eval_metrics["rmse"],
        within_absolute_05=eval_metrics["within_absolute_05"],
    )

    # Step 9: Save model
    model_version = "v1"
    save_model(model, model_version)

    logger.info(
        "Model saved successfully",
        version=model_version,
        within_absolute_05=eval_metrics["within_absolute_05"],
    )

    print("\n" + "=" * 50)
    print("TRAINING SUMMARY")
    print("=" * 50)
    print(f"Total training rows:           {len(combined_df)}")
    print(f"Training sequences:            {len(X_train)}")
    print(f"Validation sequences:          {len(X_val)}")
    print(f"Total epochs trained:          {len(history['train_loss'])}")
    print(f"Best val loss:                 {min(history['val_loss']):.6f}")
    print(f"MAE:                           {eval_metrics['mae']:.6f}")
    print(f"RMSE:                          {eval_metrics['rmse']:.6f}")
    print(f"Within 0.05 absolute:          {eval_metrics['within_absolute_05']:.1f}%")
    print(f"Within 10% (high load only):   {eval_metrics['within_10_percent_highload']:.1f}%")
    print(f"High load samples:             {eval_metrics['high_load_samples']}")
    print(f"Model version:                 v1")
    print("=" * 50)


if __name__ == "__main__":
    main()