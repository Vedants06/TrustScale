"""Health report signing for node attestation."""

from shared.contracts.health_report import HealthReport, SignedHealthReport
from shared.crypto.jwt_utils import create_signed_token
from services.node.crypto.keypair import get_private_key, get_public_key_pem
from services.node.config.settings import settings
from shared.utils.logger import get_logger

logger = get_logger("signer")


def sign_health_report(report: HealthReport) -> SignedHealthReport:
    """Sign a health report with the node's private key.

    Args:
        report: Unsigned health report.

    Returns:
        Signed health report with JWT signature.
    """
    private_key = get_private_key()

    # Create payload from report
    payload = report.model_dump()

    # Sign the payload
    signature = create_signed_token(payload, private_key)

    signed_report = SignedHealthReport(
        report=report,
        signature=signature,
        public_key_id=settings.node_id,
    )

    logger.debug("Health report signed", node_id=report.node_id)

    return signed_report