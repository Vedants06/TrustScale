"""Redis schema helpers for quarantine state."""


def quarantine_key(node_id: str) -> str:
    """Redis key for node quarantine flag."""
    return f"quarantine:{node_id}"


def quarantine_since_key(node_id: str) -> str:
    """Redis key for quarantine start timestamp."""
    return f"quarantine_since:{node_id}"