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
    """TLS is required for Railway public proxies, not private *.railway.internal mesh."""
    host = (database_host(url) or "").lower()
    if _is_railway_internal_host(host):
        return False
    if host.endswith(".rlwy.net") or host.endswith(".railway.app"):
        return True
    return False


def running_on_railway() -> bool:
    return bool(
        os.getenv("RAILWAY_ENVIRONMENT")
        or os.getenv("RAILWAY_SERVICE_ID")
        or os.getenv("RAILWAY_PROJECT_ID")
    )


def strip_url_query_params(url: str, *params: str) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    for param in params:
        query.pop(param, None)
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


def prepare_asyncpg_dsn(url: str) -> tuple[str, dict[str, Any]]:
    """Return (dsn, extra pool kwargs). Internal mesh = plain TCP; public proxy = sslmode in DSN."""
    host = database_host(url)
    pool_kwargs: dict[str, Any] = {"statement_cache_size": 0}
    if _is_railway_internal_host(host):
        return strip_url_query_params(url, "sslmode", "ssl"), pool_kwargs
    if railway_postgres_requires_ssl(url):
        return ensure_postgres_ssl_params(url), pool_kwargs
    return url, pool_kwargs


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
                dsn, _ = prepare_asyncpg_dsn(pub_url)
                return dsn, meta
            continue
        if host_resolves(host):
            meta.update({"selected_env": key, "selected_host": host, "selection": "resolvable"})
            dsn, _ = prepare_asyncpg_dsn(url)
            return dsn, meta

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
        dsn, _ = prepare_asyncpg_dsn(pub_url)
        return dsn, meta

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
    dsn, _ = prepare_asyncpg_dsn(url)
    return dsn, meta


def expand_asyncpg_pool_targets(key: str, url: str) -> list[tuple[str, str, dict[str, Any]]]:
    """One env URL may map to several asyncpg SSL strategies (Railway public proxy)."""
    host = database_host(url)
    base_kwargs: dict[str, Any] = {"statement_cache_size": 0}
    if railway_postgres_requires_ssl(url):
        stripped = strip_url_query_params(url, "sslmode", "ssl")
        import ssl

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return [
            (f"{key}+sslmode", ensure_postgres_ssl_params(url), dict(base_kwargs)),
            (f"{key}+ssl_true", stripped, {**base_kwargs, "ssl": True}),
            (f"{key}+ssl_ctx", stripped, {**base_kwargs, "ssl": ctx}),
        ]
    if _is_railway_internal_host(host):
        return [(key, strip_url_query_params(url, "sslmode", "ssl"), dict(base_kwargs))]
    dsn, pool_kwargs = prepare_asyncpg_dsn(url)
    return [(key, dsn, pool_kwargs)]


def iter_asyncpg_pool_candidates() -> list[tuple[str, str, dict[str, Any]]]:
    """Ordered (env_key, dsn, pool_kwargs) for asyncpg pool creation fallbacks."""
    candidates = candidate_database_urls()
    ordered: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    def _add(key: str, url: str) -> None:
        if url in seen_urls:
            return
        seen_urls.add(url)
        ordered.append((key, url))

    if running_on_railway():
        for key, url in candidates:
            if _is_railway_internal_host(database_host(url)):
                _add(key, url)
    for key, url in candidates:
        host = database_host(url)
        if _is_railway_internal_host(host) and not host_resolves(host):
            continue
        if host_resolves(host) or _is_railway_internal_host(host):
            _add(key, url)
    for key, url in candidates:
        _add(key, url)

    out: list[tuple[str, str, dict[str, Any]]] = []
    seen: set[tuple[str, frozenset[tuple[str, Any]]]] = set()
    for key, url in ordered:
        for cand_key, dsn, pool_kwargs in expand_asyncpg_pool_targets(key, url):
            sig = (dsn, frozenset(pool_kwargs.items()))
            if sig in seen:
                continue
            seen.add(sig)
            out.append((cand_key, dsn, pool_kwargs))
    return out
