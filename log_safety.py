"""Sanitize untrusted / sensitive values before logging (S5145 / CodeQL CWE-312)."""

from __future__ import annotations

import hashlib
import os
import re
from typing import Any, Iterable

_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
_ALLOWED_ASSET = re.compile(r"^[A-Za-z0-9._:/-]{1,64}$")
_SECRETISH = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|authorization|bearer|"
    r"cookie|session|private[_-]?key|webhook|dsn|connection[_-]?string|"
    r"postgres(ql)?://|mysql://|redis://|mongodb(\+srv)?://)"
)


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
    if _SECRETISH.search(text):
        return "[redacted]"
    if len(text) > max_len:
        text = text[: max_len - 1] + "…"
    return text or "-"


def sanitize_asset(value: Any) -> str:
    text = sanitize_log_value(value, max_len=32)
    if _ALLOWED_ASSET.fullmatch(text):
        return text
    return "invalid_asset"


def env_configured(name: str) -> bool:
    """True when env var is non-empty — never returns or propagates the value."""
    raw = os.environ.get(name)
    if raw is None:
        return False
    return len(raw.strip()) > 0


def env_digest(name: str) -> str:
    """SHA-256 hex of stripped env value, or empty string when unset.

    Used to compare against known-insecure default digests without retaining
    clear-text secret material in caller state.
    """
    raw = os.environ.get(name)
    if raw is None:
        return ""
    text = raw.strip().lower()
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


def redact_secret(value: Any) -> str:
    """Always-redact helper for sinks that must never emit credentials."""
    if value is None or value == "":
        return "[unset]"
    return "[redacted]"


def untainted_catalog_ids(selected: Iterable[str], catalog: tuple[str, ...]) -> list[str]:
    """Re-emit ids exclusively from a literal catalog (breaks secret container taint)."""
    wanted = {str(x) for x in selected}
    return [cid for cid in catalog if cid in wanted]
