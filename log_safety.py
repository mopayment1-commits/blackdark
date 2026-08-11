"""Sanitize untrusted values before logging (Sonar S5145 / CodeQL py/log-injection)."""

from __future__ import annotations

import re
from typing import Any

_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
_ALLOWED_ASSET = re.compile(r"^[A-Za-z0-9._:/-]{1,64}$")


def sanitize_log_value(value: Any, *, max_len: int = 64) -> str:
    """Return a log-safe scalar representation (no raw user/control content)."""
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    # Explicit CR/LF replace is required for CodeQL py/log-injection recognition.
    text = str(value).replace("\r", " ").replace("\n", " ")
    text = _CONTROL.sub("", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text or "-"


def sanitize_asset(value: Any) -> str:
    text = sanitize_log_value(value, max_len=32)
    if _ALLOWED_ASSET.fullmatch(text):
        return text
    return "invalid_asset"
