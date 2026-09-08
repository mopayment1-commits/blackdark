"""Password policy — ID-003, ID-004 (NIST 800-63B-4 aligned)."""

from __future__ import annotations

import os
import unicodedata

_COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "12345678",
    "123456789",
    "1234567890",
    "123456789012345",
    "qwerty123",
    "letmein1",
    "welcome1",
    "admin123",
    "blackdark",
    "trustos1",
    "iloveyou",
    "abc12345",
    "correcthorsebatterystaple",
}

PASSWORD_MIN_LENGTH = int(os.getenv("IDENTITY_PASSWORD_MIN_LENGTH", "15"))
PASSWORD_MAX_LENGTH = int(os.getenv("IDENTITY_PASSWORD_MAX_LENGTH", "128"))


def normalize_password(password: str) -> str:
    """NFC-normalize Unicode passwords before hashing (ID-004)."""
    return unicodedata.normalize("NFC", password or "")


def validate_password_policy(password: str, *, email: str = "") -> None:
    pwd = normalize_password(password)
    if len(pwd) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(pwd) > PASSWORD_MAX_LENGTH:
        raise ValueError(f"Password must be at most {PASSWORD_MAX_LENGTH} characters")
    blocked = set(_COMMON_PASSWORDS)
    extra = os.getenv("IDENTITY_BLOCKED_PASSWORDS", "")
    if extra:
        blocked.update(x.strip().lower() for x in extra.split(",") if x.strip())
    if pwd.lower() in blocked:
        raise ValueError("Password is too common — choose a stronger one")
    local = (email or "").split("@")[0].lower()
    if local and len(local) >= 4 and local in pwd.lower():
        raise ValueError("Password must not contain your email local-part")
    if pwd.isdigit():
        raise ValueError("Password must not be only numbers")
