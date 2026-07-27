"""RSA key pair management for node identity."""

from cryptography.hazmat.primitives.asymmetric import rsa

from shared.crypto.key_generation import generate_rsa_keypair, serialize_public_key
from shared.crypto.serialization import serialize_private_key
from shared.utils.logger import get_logger

logger = get_logger("keypair")

_private_key: rsa.RSAPrivateKey | None = None
_public_key: rsa.RSAPublicKey | None = None


def initialize_keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Initialize the node's RSA key pair.

    Returns:
        Tuple of (private_key, public_key).
    """
    global _private_key, _public_key

    _private_key, _public_key = generate_rsa_keypair()
    logger.info("RSA key pair generated")

    return _private_key, _public_key


def get_private_key() -> rsa.RSAPrivateKey:
    """Get the node's private key.

    Returns:
        RSA private key.

    Raises:
        RuntimeError: If key pair not initialized.
    """
    if _private_key is None:
        raise RuntimeError("Key pair not initialized. Call initialize_keypair() first.")
    return _private_key


def get_public_key() -> rsa.RSAPublicKey:
    """Get the node's public key.

    Returns:
        RSA public key.

    Raises:
        RuntimeError: If key pair not initialized.
    """
    if _public_key is None:
        raise RuntimeError("Key pair not initialized. Call initialize_keypair() first.")
    return _public_key


def get_public_key_pem() -> str:
    """Get the node's public key as PEM string.

    Returns:
        PEM-encoded public key string.
    """
    return serialize_public_key(get_public_key())