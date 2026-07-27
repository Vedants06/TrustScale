"""Private key serialization utilities."""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization


def serialize_private_key(private_key: rsa.RSAPrivateKey) -> str:
    """Serialize an RSA private key to PEM string (unencrypted).

    Args:
        private_key: RSA private key object.

    Returns:
        PEM-encoded private key as string.

    Warning:
        This serializes without encryption.
        Suitable for development and container-internal use only.
    """
    pem_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem_bytes.decode("utf-8")


def deserialize_private_key(key_str: str) -> rsa.RSAPrivateKey:
    """Deserialize a PEM string to RSA private key.

    Args:
        key_str: PEM-encoded private key string.

    Returns:
        RSA private key object.
    """
    key = serialization.load_pem_private_key(
        key_str.encode("utf-8"),
        password=None,
    )
    if not isinstance(key, rsa.RSAPrivateKey):
        raise ValueError("Key is not an RSA private key")
    return key