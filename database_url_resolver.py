"""Resolve PostgreSQL DSN from Railway / platform environment variables."""

from __future__ import annotations

import os
import socket
from typing import Any
from urllib.parse import urlparse

_CANDIDATE_KEYS: tuple[str, ...] = (
    "DATABASE_URL",
    "DATABASE_PRIVATE_URL",
    "DATABASE_PUBLIC_URL",
    "POSTGRES_URL",
    "PGDATABASE_URL",
    "RAILWAY_DATABASE_URL",
)


def _normalize(url: str) -> str:
    value = (url or "").strip()
    if value.startswith("postgres://"):
        return "postgresql://" + value[len("postgres://") :]
    return value


def candidate_database_urls() -> list[tuple[str, str]]:
    """Return (env_key, normalized_url) pairs in priority order."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for key in _CANDIDATE_KEYS:
        raw = os.getenv(key, "").strip()
        if not raw:
            continue
        url = _normalize(raw)
        if not url.startswith("postgresql://"):
            continue
        if url in seen:
            continue
        seen.add(url)
        out.append((key, url))
    return out


def database_host(url: str) -> str | None:
    try:
        return urlparse(url).hostname
    except Exception:
        return None


def host_resolves(host: str | None, *, timeout: float = 2.0) -> bool:
    if not host:
        return False
    prev = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        socket.getaddrinfo(host, None)
        return True
    except OSError:
        return False
    finally:
        socket.setdefaulttimeout(prev)


def resolve_database_url() -> tuple[str | None, dict[str, Any]]:
    """Pick the first DSN whose hostname resolves; fall back to first candidate."""
    candidates = candidate_database_urls()
    meta: dict[str, Any] = {
        "candidates": [
            {"env": key, "host": database_host(url), "resolves": host_resolves(database_host(url))}
            for key, url in candidates
        ],
        "selected_env": None,
        "selected_host": None,
        "selection": "none",
    }
    if not candidates:
        return None, meta

    for key, url in candidates:
        host = database_host(url)
        if host_resolves(host):
            meta.update({"selected_env": key, "selected_host": host, "selection": "resolvable"})
            return url, meta

    key, url = candidates[0]
    meta.update({"selected_env": key, "selected_host": database_host(url), "selection": "first_candidate_unresolved"})
    return url, meta
