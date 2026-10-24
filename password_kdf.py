"""
Password hashing — Argon2id (OWASP/NIST-aligned), bcrypt fallback, legacy PBKDF2 verify.

New passwords: Argon2id with m≥19 MiB, t≥2, p=1; salt ≥128 bits inside Argon2/bcrypt.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from typing import Final

logger = logging.getLogger("BLACKDARK.PasswordKDF")

# 19 MiB expressed as KiB for argon2-cffi memory_cost
_ARGON2_MEMORY_KIB: Final[int] = 19 * 1024
_ARGON2_TIME: Final[int] = 2
_ARGON2_PARALLELISM: Final[int] = 1
_BCRYPT_ROUNDS: Final[int] = 12
_PBKDF2_ITERATIONS: Final[int] = 260_000


def _argon2_hasher():
    from argon2 import PasswordHasher

    return PasswordHasher(
        memory_cost=_ARGON2_MEMORY_KIB,
        time_cost=_ARGON2_TIME,
        parallelism=_ARGON2_PARALLELISM,
        hash_len=32,
        salt_len=16,
    )


def hash_password(password: str) -> str:
    try:
        ph = _argon2_hasher()
        digest = ph.hash(password)
        return f"argon2id${digest}"
    except Exception:
        logger.debug("argon2 unavailable — trying bcrypt", exc_info=True)
    try:
        import bcrypt

        salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
        digest = bcrypt.hashpw(password.encode("utf-8"), salt)
        return f"bcrypt${digest.decode('ascii')}"
    except Exception:
        logger.warning("bcrypt unavailable — using PBKDF2 (install argon2-cffi)", exc_info=True)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        _PBKDF2_ITERATIONS,
    )
    return f"pbkdf2_sha256${_PBKDF2_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    stored = (stored or "").strip()
    if not stored:
        return False
    if stored.startswith("argon2id$"):
        try:
            ph = _argon2_hasher()
            ph.verify(stored.split("$", 1)[1], password)
            return True
        except Exception:
            return False
    if stored.startswith("bcrypt$"):
        try:
            import bcrypt

            return bcrypt.checkpw(
                password.encode("utf-8"),
                stored.split("$", 1)[1].encode("ascii"),
            )
        except Exception:
            return False
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


def password_needs_rehash(stored: str) -> bool:
    stored = (stored or "").strip()
    if not stored.startswith("argon2id$"):
        return True
    try:
        ph = _argon2_hasher()
        return ph.check_needs_rehash(stored.split("$", 1)[1])
    except Exception:
        return True
