"""LSTM model architecture for load prediction."""

import torch
import torch.nn as nn

from shared.utils.logger import get_logger

logger = get_logger("lstm_model")


class LSTMLoadPredictor(nn.Module):
    """LSTM neural network for predicting node load.

    Architecture:
        Input: sequence of composite load values
        LSTM layers: learn temporal patterns
        Fully connected: map to single load prediction
        Sigmoid: constrain output to 0-1 range
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.2,
    ) -> None:
        super().__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )

        self.fc = nn.Linear(hidden_size, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size).

        Returns:
            Predicted load tensor of shape (batch_size, 1).
        """
        lstm_out, _ = self.lstm(x)
        last_hidden = lstm_out[:, -1, :]
        output = self.fc(last_hidden)
        return self.sigmoid(output)