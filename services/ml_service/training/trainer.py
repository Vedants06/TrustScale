"""LSTM training loop."""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from shared.utils.logger import get_logger

logger = get_logger("trainer")


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 50,
    learning_rate: float = 0.001,
    patience: int = 10,
) -> dict[str, list[float]]:
    """Train the LSTM model with early stopping.

    Args:
        model: LSTM model to train.
        train_loader: Training data loader.
        val_loader: Validation data loader.
        epochs: Maximum number of training epochs.
        learning_rate: Adam optimizer learning rate.
        patience: Early stopping patience in epochs.

    Returns:
        Dictionary with training and validation loss history.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    history: dict[str, list[float]] = {
        "train_loss": [],
        "val_loss": [],
    }

    best_val_loss = float("inf")
    patience_counter = 0
    best_state_dict = None

    for epoch in range(epochs):
        # Training
        model.train()
        train_losses: list[float] = []

        for X_batch, y_batch in train_loader:
            optimizer.zero_grad()
            predictions = model(X_batch)
            loss = criterion(predictions, y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_losses.append(loss.item())

        avg_train_loss = sum(train_losses) / len(train_losses)

        # Validation
        model.eval()
        val_losses: list[float] = []

        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                predictions = model(X_batch)
                loss = criterion(predictions, y_batch)
                val_losses.append(loss.item())

        avg_val_loss = sum(val_losses) / len(val_losses)

        history["train_loss"].append(avg_train_loss)
        history["val_loss"].append(avg_val_loss)

        logger.info(
            "Epoch complete",
            epoch=epoch + 1,
            train_loss=round(avg_train_loss, 6),
            val_loss=round(avg_val_loss, 6),
        )

        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            best_state_dict = {
                k: v.clone() for k, v in model.state_dict().items()
            }
        else:
            patience_counter += 1

        if patience_counter >= patience:
            logger.info(
                "Early stopping triggered",
                epoch=epoch + 1,
                best_val_loss=round(best_val_loss, 6),
            )
            break

    # Restore best weights
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)

    logger.info(
        "Training complete",
        best_val_loss=round(best_val_loss, 6),
        total_epochs=len(history["train_loss"]),
    )

    return history