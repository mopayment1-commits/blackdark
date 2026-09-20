"""
BLACKDARK — Password policy, Argon2id storage, breach checks (ID-003…006).

P0 scope: NFC normalization, Argon2id hashing, legacy PBKDF2 verify + rehash-on-login,
local blocklist, optional HIBP k-anonymity when available.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import unicodedata
from typing import Any

logger = logging.getLogger("BLACKDARK.PasswordSecurity")

PASSWORD_MIN_LENGTH = int(os.getenv("IDENTITY_PASSWORD_MIN_LENGTH", "15"))
PASSWORD_MAX_LENGTH = 128
PRIMARY_HASH_SCHEME = "argon2id"
PBKDF2_ITERATIONS = 260_000

_COMMON_PASSWORDS = {
    "password",
    "password1",
    "password123",
    "password1234567890",
    "12345678",
    "123456789",
    "1234567890",
    "qwerty123",
    "letmein1",
    "welcome1",
    "admin123",
    "blackdark",
    "trustos1",
    "iloveyou",
    "abc12345",
}

_FORBIDDEN_HASH_PREFIXES = (
    "md5$",
    "sha1$",
    "sha-1$",
    "sha256$",
    "sha-256$",
    "sha512$",
    "sha-512$",
    "plaintext$",
)


def normalize_password_nfc(password: str) -> str:
    """ID-004 — Unicode NFC normalization before hashing or policy checks."""
    return unicodedata.normalize("NFC", password or "")


def _blocked_password_set() -> set[str]:
    blocked = set(_COMMON_PASSWORDS)
    extra = os.getenv("IDENTITY_BLOCKED_PASSWORDS", "")
    if extra:
        blocked.update(x.strip().lower() for x in extra.split(",") if x.strip())
    return blocked


def _hibp_enabled() -> bool:
    raw = os.getenv("IDENTITY_HIBP_CHECK", "auto").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    if raw in {"1", "true", "yes", "on"}:
        return True
    return True


def check_breached_password(password: str) -> dict[str, Any]:
    """ID-005 — HIBP k-anonymity when reachable; else local-only + BLOCKED_EXTERNAL."""
    if not _hibp_enabled():
        return {
            "breached": False,
            "source": "local_only",
            "hibp_status": "BLOCKED_EXTERNAL",
            "detail": "External breach API disabled",
        }
    try:
        import urllib.request

        digest = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = digest[:5], digest[5:]
        url = f"https://api.pwnedpasswords.com/range/{prefix}"
        req = urllib.request.Request(url, headers={"User-Agent": "BLACKDARK-Identity-P0"})
        with urllib.request.urlopen(req, timeout=float(os.getenv("IDENTITY_HIBP_TIMEOUT_SEC", "2.0"))) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
        for line in body.splitlines():
            part, count = line.split(":", 1)
            if part.strip().upper() == suffix:
                return {
                    "breached": True,
                    "source": "hibp",
                    "hibp_status": "KNOWN",
                    "exposure_count": int(count.strip()),
                }
        return {"breached": False, "source": "hibp", "hibp_status": "KNOWN"}
    except Exception as exc:
        logger.debug("HIBP breach check unavailable: %s", exc)
        return {
            "breached": False,
            "source": "local_only",
            "hibp_status": "BLOCKED_EXTERNAL",
            "detail": str(exc),
        }


def validate_password_policy(password: str, *, email: str = "") -> dict[str, Any]:
    """ID-003/005 — length, local blocklist, optional breach check. No composition rules."""
    pwd = normalize_password_nfc(password)
    if len(pwd) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(pwd) > PASSWORD_MAX_LENGTH:
        raise ValueError("Password too long")
    lowered = pwd.lower().strip()
    if lowered in _blocked_password_set():
        raise ValueError("Password is too common — choose a stronger one")
    local = (email or "").split("@")[0].lower()
    if local and len(local) >= 4 and local in lowered:
        raise ValueError("Password must not contain your email local-part")
    if pwd.isdigit():
        raise ValueError("Password must not be only numbers")
    breach = check_breached_password(pwd)
    if breach.get("breached"):
        raise ValueError("Password appeared in a known breach — choose a different one")
    return {
        "normalized": pwd,
        "min_length": PASSWORD_MIN_LENGTH,
        "breach_check": breach,
        "hash_scheme": PRIMARY_HASH_SCHEME,
    }


def _argon2_hasher():
    from argon2 import PasswordHasher

    return PasswordHasher(
        time_cost=int(os.getenv("ARGON2_TIME_COST", "3")),
        memory_cost=int(os.getenv("ARGON2_MEMORY_KIB", "65536")),
        parallelism=int(os.getenv("ARGON2_PARALLELISM", "4")),
        hash_len=32,
        salt_len=16,
    )


def hash_password(password: str) -> str:
    """ID-006 — Argon2id with unique salt (PHC string)."""
    pwd = normalize_password_nfc(password)
    return _argon2_hasher().hash(pwd)


def _verify_pbkdf2(password: str, stored: str) -> bool:
    try:
        scheme, iterations, salt, digest_hex = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        )
        return hmac.compare_digest(expected.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def is_weak_hash_rejected(stored: str) -> bool:
    """True when stored hash uses a forbidden weak scheme."""
    lowered = (stored or "").strip().lower()
    return any(lowered.startswith(prefix) for prefix in _FORBIDDEN_HASH_PREFIXES)


def verify_password_detailed(password: str, stored: str) -> tuple[bool, bool]:
    """
    Verify password against stored hash.

    Returns (ok, needs_rehash). Legacy PBKDF2 verifies but requests rehash on success.
    Weak schemes always fail.
    """
    if not stored or is_weak_hash_rejected(stored):
        return False, False
    pwd = normalize_password_nfc(password)
    if stored.startswith("pbkdf2_sha256$"):
        ok = _verify_pbkdf2(pwd, stored)
        return ok, ok
    if stored.startswith("$argon2"):
        from argon2.exceptions import VerifyMismatchError

        hasher = _argon2_hasher()
        try:
            hasher.verify(stored, pwd)
            return True, hasher.check_needs_rehash(stored)
        except VerifyMismatchError:
            return False, False
    return False, False


def verify_password(password: str, stored: str) -> bool:
    ok, _ = verify_password_detailed(password, stored)
    return ok


def password_policy_metadata() -> dict[str, Any]:
    return {
        "min_length": PASSWORD_MIN_LENGTH,
        "max_length": PASSWORD_MAX_LENGTH,
        "hash": PRIMARY_HASH_SCHEME,
        "composition_rules": False,
        "unicode_nfc": True,
        "breach_check": "hibp_k_anonymity_when_available",
    }
