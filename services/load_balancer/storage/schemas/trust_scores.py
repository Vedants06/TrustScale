"""Redis schema helpers for trust score state."""


def trust_score_key(node_id: str) -> str:
    """Redis key for node trust score."""
    return f"trust:{node_id}"