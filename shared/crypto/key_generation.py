"""RSA key pair generation for node identity and signing."""

from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization


def generate_rsa_keypair() -> tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
    """Generate a 2048-bit RSA key pair.

    Returns:
        Tuple of (private_key, public_key).
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    return private_key, public_key


def serialize_public_key(public_key: rsa.RSAPublicKey) -> str:
    """Serialize an RSA public key to PEM string.

    Args:
        public_key: RSA public key object.

    Returns:
        PEM-encoded public key as string.
    """
    pem_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return pem_bytes.decode("utf-8")


def deserialize_public_key(key_str: str) -> rsa.RSAPublicKey:
    """Deserialize a PEM string to RSA public key.

    Args:
        key_str: PEM-encoded public key string.

    Returns:
        RSA public key object.
    """
    key = serialization.load_pem_public_key(key_str.encode("utf-8"))
    if not isinstance(key, rsa.RSAPublicKey):
        raise ValueError("Key is not an RSA public key")
    return key