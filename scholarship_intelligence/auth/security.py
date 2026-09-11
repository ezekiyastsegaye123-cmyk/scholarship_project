"""Security and authentication utilities for student accounts.

Enforces:
- Modern adaptive password hashing using hashlib.scrypt (RFC 7914).
- Secure random salt generation per password.
- Constant-time password verification (secrets.compare_digest).
- Cryptographically signed HMAC-SHA256 bearer session tokens.
- Strict token expiration and signature validation.
- No plaintext password storage, logging, or leakage.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "scholarship-intelligence-dev-secret-key-change-in-prod")
TOKEN_EXPIRATION_HOURS = int(os.getenv("TOKEN_EXPIRATION_HOURS", "72"))
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

# Scrypt parameters (OWASP / NIST recommended)
SCRYPT_N = 16384  # CPU/memory cost
SCRYPT_R = 8      # Block size
SCRYPT_P = 1      # Parallelization parameter
SALT_BYTES = 16
HASH_BYTES = 64


class AuthenticationError(ValueError):
    """Raised when authentication credentials or tokens are invalid."""
    pass


def normalize_email(email: str) -> str:
    """Normalizes email address for consistent, canonical identity checks."""
    if not email or not isinstance(email, str):
        raise AuthenticationError("Email must be a valid non-empty string.")
    normalized = email.strip().lower()
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, normalized) or len(normalized) > 255:
        raise AuthenticationError("Invalid email address format.")
    return normalized


def validate_password_strength(password: str) -> None:
    """Enforces minimum password security constraints."""
    if not password or not isinstance(password, str):
        raise AuthenticationError("Password must be a non-empty string.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthenticationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise AuthenticationError(f"Password exceeds maximum allowed length of {MAX_PASSWORD_LENGTH} characters.")


def hash_password(password: str) -> str:
    """Hashes password using scrypt with a unique cryptographically secure salt."""
    validate_password_strength(password)
    salt = secrets.token_bytes(SALT_BYTES)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        maxmem=0,
        dklen=HASH_BYTES,
    )
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(derived).decode("ascii")
    return f"$scrypt$ln=14,r={SCRYPT_R},p={SCRYPT_P}${salt_b64}${hash_b64}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a plaintext password against an scrypt hash in constant time."""
    if not password or not stored_hash:
        return False
    try:
        parts = stored_hash.split("$")
        # Expected format: ["", "scrypt", "ln=14,r=8,p=1", salt_b64, hash_b64]
        if len(parts) != 5 or parts[1] != "scrypt":
            return False
        salt = base64.b64decode(parts[3].encode("ascii"))
        expected_hash = base64.b64decode(parts[4].encode("ascii"))

        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            maxmem=0,
            dklen=len(expected_hash),
        )
        return secrets.compare_digest(derived, expected_hash)
    except Exception:
        return False


def create_access_token(account_id: str, email: str, expires_delta: Optional[timedelta] = None) -> Tuple[str, datetime]:
    """Generates a tamper-proof HMAC-SHA256 signed access token."""
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(hours=TOKEN_EXPIRATION_HOURS)
    expires_at = now + delta

    payload = {
        "sub": account_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": secrets.token_hex(16),
    }

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_json).decode("ascii").rstrip("=")

    signature = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")

    token = f"{payload_b64}.{sig_b64}"
    return token, expires_at


def decode_access_token(token: str) -> Dict[str, Any]:
    """Validates signature and expiration of an access token, returning the payload."""
    if not token or not isinstance(token, str):
        raise AuthenticationError("Invalid authentication token.")

    parts = token.split(".")
    if len(parts) != 2:
        raise AuthenticationError("Malformed authentication token.")

    payload_b64, sig_b64 = parts[0], parts[1]

    # Recompute signature
    expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("ascii"), hashlib.sha256).digest()
    expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode("ascii").rstrip("=")

    if not secrets.compare_digest(sig_b64, expected_sig_b64):
        raise AuthenticationError("Invalid token signature.")

    # Decode payload
    try:
        # Add back required base64 padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise AuthenticationError(f"Failed to decode token payload: {e}") from e

    # Check expiration
    exp = payload.get("exp")
    if not exp or not isinstance(exp, (int, float)):
        raise AuthenticationError("Token missing expiration claim.")

    now_ts = datetime.now(timezone.utc).timestamp()
    if now_ts > exp:
        raise AuthenticationError("Token has expired.")

    return payload
