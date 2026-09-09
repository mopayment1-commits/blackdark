"""Stable non-sequential public user identifiers — ID-001 external surface."""

from __future__ import annotations

import re
from uuid import uuid4

_PUBLIC_ID_RE = re.compile(r"^u_[0-9a-f]{32}$")


def generate_public_user_id() -> str:
    return f"u_{uuid4().hex}"


def generate_user_uuid() -> str:
    return str(uuid4())


def is_valid_public_user_id(value: str | None) -> bool:
    return bool(value and _PUBLIC_ID_RE.fullmatch(str(value)))


def default_avatar_url(public_user_id: str) -> str:
    return f"/api/auth/avatar/{public_user_id}.svg"
