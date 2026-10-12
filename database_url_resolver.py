"""Resolve PostgreSQL DSN from Railway / platform environment variables."""

from __future__ import annotations

import os
import socket
from typing import Any
from urllib.parse import parse_qsl, urlparse, urlencode, urlunparse

_CANDIDATE_KEYS: tuple[str, ...] = (
    "DATABASE_URL",
    "DATABASE_PRIVATE_URL",
    "DATABASE_PUBLIC_URL",
    "POSTGRES_URL",
    "PGDATABASE_URL",
    "RAILWAY_DATABASE_URL",
    "BLACKDARK_TEST_DATABASE_URL",
)


def _normalize(url: str) -> str:
    value = (url or "").strip()
    if value.startswith("postgres://"):
        return "postgresql://" + value[len("postgres://") :]
    return value


def _is_railway_internal_host(host: str | None) -> bool:
    return bool(host) and host.lower().endswith(".railway.internal")


def _canonicalize_railway_internal_host(url: str) -> str:
    """Railway private DNS hostnames must be lowercase (service name)."""
    parsed = urlparse(url)
    host = parsed.hostname
    if not host or not _is_railway_internal_host(host):
        return url
    lower = host.lower()
    port = f":{parsed.port}" if parsed.port else ""
    userinfo = ""
    if parsed.username:
        userinfo = parsed.username
        if parsed.password:
            userinfo += f":{parsed.password}"
        userinfo += "@"
    netloc = f"{userinfo}{lower}{port}"
    return urlunparse(
        (parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment)
    )


def candidate_database_urls() -> list[tuple[str, str]]:
    """Return (env_key, normalized_url) pairs in priority order."""
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for key in _CANDIDATE_KEYS:
        raw = os.getenv(key, "").strip()
        if not raw:
            continue
        url = _canonicalize_railway_internal_host(_normalize(raw))
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


def railway_postgres_requires_ssl(url: str) -> bool:
    host = (database_host(url) or "").lower()
    if host.endswith(".rlwy.net") or host.endswith(".railway.app"):
        return True
    return _is_railway_internal_host(host)


def ensure_postgres_ssl_params(url: str) -> str:
    """Railway public Postgres proxies require TLS when sslmode is omitted."""
    parsed = urlparse(url)
    if parsed.scheme not in ("postgresql", "postgres"):
        return url
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    mode = str(query.get("sslmode") or "").lower()
    if mode == "disable" or not railway_postgres_requires_ssl(url):
        return url
    if mode:
        return url
    query["sslmode"] = "require"
    return urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query),
            parsed.fragment,
        )
    )


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

    public_pair = next(((k, u) for k, u in candidates if k == "DATABASE_PUBLIC_URL"), None)

    for key, url in candidates:
        host = database_host(url)
        if _is_railway_internal_host(host) and not host_resolves(host):
            # Railway: do not use unresolved *.railway.internal when a public DSN exists.
            if public_pair and key == "DATABASE_URL":
                pub_key, pub_url = public_pair
                pub_host = database_host(pub_url)
                meta.update(
                    {
                        "selected_env": pub_key,
                        "selected_host": pub_host,
                        "selection": "railway_public_over_unresolved_internal",
                    }
                )
                return ensure_postgres_ssl_params(pub_url), meta
            continue
        if host_resolves(host):
            meta.update({"selected_env": key, "selected_host": host, "selection": "resolvable"})
            return ensure_postgres_ssl_params(url), meta

    if public_pair:
        pub_key, pub_url = public_pair
        pub_host = database_host(pub_url)
        meta.update(
            {
                "selected_env": pub_key,
                "selected_host": pub_host,
                "selection": "railway_public_fallback",
            }
        )
        return ensure_postgres_ssl_params(pub_url), meta

    key, url = candidates[0]
    host = database_host(url)
    if _is_railway_internal_host(host):
        meta.update(
            {
                "selected_env": key,
                "selected_host": host,
                "selection": "railway_internal_unresolved_no_public",
            }
        )
        return None, meta

    meta.update({"selected_env": key, "selected_host": host, "selection": "first_candidate_unresolved"})
    return ensure_postgres_ssl_params(url), meta
