"""Redis schema helpers for prediction state."""


def prediction_key(node_id: str) -> str:
    """Redis key for cached prediction value."""
    return f"prediction:{node_id}"