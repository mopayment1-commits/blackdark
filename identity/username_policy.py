"""Username policy — ID-017, ID-018, ID-019, ID-062."""

from __future__ import annotations

import re
import unicodedata

USERNAME_MIN = 3
USERNAME_MAX = 30
USERNAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,29}$")

RESERVED_USERNAMES = frozenset(
    {
        "admin",
        "administrator",
        "api",
        "support",
        "blackdark",
        "official",
        "moderator",
        "mod",
        "oracle",
        "whale",
        "system",
        "root",
        "null",
        "undefined",
        "login",
        "signup",
        "profile",
        "billing",
        "security",
        "help",
        "staff",
        "team",
    }
)


def canonical_username(username: str) -> str:
    return (username or "").strip().lower()


def username_skeleton(username: str) -> str:
    """Confusable skeleton for impersonation checks (ID-018)."""
    u = canonical_username(username)
    out: list[str] = []
    for ch in u:
        if ch in {"0", "o"}:
            out.append("o")
        elif ch in {"1", "l", "i"}:
            out.append("i")
        elif ch in {"_", "-", "."}:
            continue
        else:
            out.append(ch)
    return "".join(out)


def validate_username(username: str, *, existing_skeletons: set[str] | None = None) -> str:
    u = canonical_username(username)
    if not USERNAME_RE.match(u):
        raise ValueError(
            f"Username must be {USERNAME_MIN}–{USERNAME_MAX} chars, start with a letter, a-z/0-9/_"
        )
    if u in RESERVED_USERNAMES:
        raise ValueError("Username is reserved")
    sk = username_skeleton(u)
    if existing_skeletons and sk in existing_skeletons:
        raise ValueError("Username too similar to an existing handle")
    if any(unicodedata.category(c) == "Mn" for c in u):
        raise ValueError("Username must use plain ASCII letters")
    return u
