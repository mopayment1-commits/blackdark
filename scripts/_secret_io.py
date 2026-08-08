"""Shared helpers for operator scripts — never echo secrets; write mode 0600."""

from __future__ import annotations

import os
from pathlib import Path


def mask_secret(value: str, *, keep: int = 4) -> str:
    raw = str(value or "")
    if not raw:
        return "(empty)"
    if len(raw) <= keep * 2:
        return "***"
    return f"{raw[:keep]}…{raw[-keep:]} (hidden)"


def write_private_text(path: Path, text: str) -> None:
    """Atomically write a private file with mode 0600 (owner read/write only)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
    os.replace(tmp, path)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def is_secret_env_key(key: str) -> bool:
    k = key.upper()
    return any(
        tok in k
        for tok in (
            "TOKEN",
            "SECRET",
            "PASSWORD",
            "API_KEY",
            "MASTER_KEY",
            "PEPPER",
            "PRIVATE",
            "WEBHOOK_SECRET",
        )
    )
