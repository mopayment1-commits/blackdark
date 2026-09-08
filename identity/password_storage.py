"""Password storage — ID-006 Argon2id with PBKDF2 migration."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from identity.password_policy import normalize_password

ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 65536
ARGON2_PARALLELISM = 2


def hash_password(password: str) -> str:
    from argon2 import PasswordHasher

    pwd = normalize_password(password)
    ph = PasswordHasher(
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=32,
        salt_len=16,
    )
    digest = ph.hash(pwd)
    return f"argon2id${digest}"


def verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """Return (valid, needs_rehash)."""
    pwd = normalize_password(password)
    if stored.startswith("argon2id$"):
        from argon2 import PasswordHasher
        from argon2.exceptions import VerifyMismatchError

        ph = PasswordHasher()
        try:
            ph.verify(stored.split("$", 1)[1], pwd)
            return True, ph.check_needs_rehash(stored.split("$", 1)[1])
        except VerifyMismatchError:
            return False, False
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt, digest_hex = stored.split("$", 3)
            expected = hashlib.pbkdf2_hmac(
                "sha256",
                pwd.encode("utf-8"),
                salt.encode("utf-8"),
                int(iterations),
            )
            ok = hmac.compare_digest(expected.hex(), digest_hex)
            return ok, ok
        except (ValueError, TypeError):
            return False, False
    return False, False


def password_scheme(stored: str) -> str:
    if stored.startswith("argon2id$"):
        return "argon2id"
    if stored.startswith("pbkdf2_sha256$"):
        return "pbkdf2_sha256"
    return "unknown"


def maybe_rehash_password(password: str, stored: str) -> str | None:
    ok, needs = verify_password(password, stored)
    if ok and needs:
        return hash_password(password)
    return None
