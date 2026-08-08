"""Public-safe error messages — never echo raw exception text to clients."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("BLACKDARK.SafeErrors")

_SENSITIVE = re.compile(
    r"(traceback|file\s*/|secret|token|password|api[_-]?key|pepper|master[_-]?key|"
    r"postgres|redis://|sqlite|/home/|/workspace/|\\\\)",
    re.IGNORECASE,
)


def public_error(
    exc: BaseException | None = None,
    *,
    fallback: str = "Request failed",
    log: bool = True,
) -> str:
    """Return a client-safe error string; log the real exception server-side."""
    if log and exc is not None:
        logger.warning("request error: %s", exc, exc_info=False)
    if exc is None:
        return fallback
    if isinstance(exc, ValueError):
        msg = str(exc.args[0]) if exc.args else fallback
        if (
            isinstance(msg, str)
            and 0 < len(msg) <= 180
            and not _SENSITIVE.search(msg)
            and "\n" not in msg
        ):
            return msg
    return fallback


def public_error_payload(
    exc: BaseException | None = None,
    *,
    fallback: str = "Request failed",
    **extra: Any,
) -> dict[str, Any]:
    out = {"error": public_error(exc, fallback=fallback), **extra}
    return out
