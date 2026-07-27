"""JWT signature verification for health reports."""

from shared.contracts.health_report import SignedHealthReport, HealthReport
from shared.crypto.jwt_utils import verify_token, is_token_expired
from shared.crypto.key_generation import deserialize_public_key
from shared.utils.logger import get_logger

logger = get_logger("verifier")


def verify_health_report(
    signed_report: SignedHealthReport,
    public_key_pem: str,
    max_age_seconds: int = 30,
) -> tuple[bool, str]:
    """Verify a signed health report.

    Args:
        signed_report: The signed health report to verify.
        public_key_pem: PEM-encoded public key of the node.
        max_age_seconds: Maximum age of the report in seconds.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is empty string.
    """
    try:
        public_key = deserialize_public_key(public_key_pem)
    except Exception as e:
        logger.error("Failed to deserialize public key", error=str(e))
        return False, "invalid_public_key"

    # Verify signature
    payload = verify_token(signed_report.signature, public_key)
    if payload is None:
        logger.warning(
            "Signature verification failed",
            node_id=signed_report.report.node_id,
        )
        return False, "invalid_signature"

    # Check timestamp freshness
    if is_token_expired(signed_report.signature, public_key, max_age_seconds):
        logger.warning(
            "Report timestamp is stale",
            node_id=signed_report.report.node_id,
        )
        return False, "timestamp_stale"

    return True, ""