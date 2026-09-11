"""Authentication and authorization package."""
from scholarship_intelligence.auth.security import (
    AuthenticationError,
    create_access_token,
    decode_access_token,
    hash_password,
    normalize_email,
    validate_password_strength,
    verify_password,
)

__all__ = [
    "AuthenticationError",
    "hash_password",
    "verify_password",
    "normalize_email",
    "validate_password_strength",
    "create_access_token",
    "decode_access_token",
]
