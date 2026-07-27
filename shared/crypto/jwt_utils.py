"""JWT signing and verification utilities for health report attestation."""

import json
import time

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from shared.crypto.key_generation import serialize_public_key
from shared.crypto.serialization import serialize_private_key


def create_signed_token(
    payload: dict,
    private_key: rsa.RSAPrivateKey,
) -> str:
    """Create a JWT signed with an RSA private key.

    Args:
        payload: Dictionary to encode in the token.
        private_key: RSA private key for signing.

    Returns:
        Signed JWT string.
    """
    token_payload = {
        **payload,
        "iat": int(time.time()),
    }
    token = jwt.encode(
        token_payload,
        key=serialize_private_key(private_key),
        algorithm="RS256",
    )
    return token


def verify_token(
    token: str,
    public_key: rsa.RSAPublicKey,
) -> dict | None:
    """Verify a JWT signature and return the payload.

    Args:
        token: JWT string to verify.
        public_key: RSA public key for verification.

    Returns:
        Decoded payload dict if valid, None if verification fails.
    """
    try:
        payload = jwt.decode(
            token,
            key=serialize_public_key(public_key),
            algorithms=["RS256"],
        )
        return payload
    except jwt.InvalidTokenError:
        return None


def is_token_expired(
    token: str,
    public_key: rsa.RSAPublicKey,
    max_age_seconds: int = 30,
) -> bool:
    """Check whether a JWT token is older than the allowed maximum age.

    Args:
        token: JWT string to check.
        public_key: RSA public key for verification.
        max_age_seconds: Maximum allowed age in seconds. Default 30.

    Returns:
        True if expired or invalid, False if still fresh.
    """
    payload = verify_token(token, public_key)
    if payload is None:
        return True

    issued_at = payload.get("iat")
    if issued_at is None:
        return True

    age = int(time.time()) - int(issued_at)
    return age > max_age_seconds