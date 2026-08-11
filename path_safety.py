"""Shared path / URL safety helpers for Sonar path-injection and SSRF rules."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

_SAFE_URL_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_SAFE_HOST_RE = re.compile(r"^[A-Za-z0-9._:\-\[\]]+$")
_DEFAULT_HTTP_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def resolve_under(base: Path | str, *parts: str) -> Path:
    """Resolve path and ensure it stays under base; raise ValueError otherwise."""
    base_resolved = Path(base).resolve()
    candidate = base_resolved.joinpath(*parts).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"Path escapes base directory: {candidate} (base={base_resolved})") from exc
    return candidate


def ensure_under(path: Path | str, base: Path | str) -> Path:
    """Resolve an existing path and ensure it stays under base."""
    base_resolved = Path(base).resolve()
    candidate = Path(path).resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ValueError(f"Path escapes base directory: {candidate} (base={base_resolved})") from exc
    return candidate


def safe_url_segment(value: str) -> str:
    """Allowlist a single URL path segment (alphanumeric, hyphen, underscore)."""
    cleaned = str(value).strip()
    if not cleaned or not _SAFE_URL_SEGMENT_RE.fullmatch(cleaned):
        raise ValueError(f"Unsafe URL path segment: {value!r}")
    return cleaned


def assert_url_path_safe(url: str) -> str:
    """Reject URLs whose path contains traversal or non-allowlisted segments."""
    parsed = urlparse(url)
    for segment in parsed.path.split("/"):
        if not segment:
            continue
        if segment in {".", ".."} or not _SAFE_URL_SEGMENT_RE.fullmatch(segment):
            raise ValueError(f"Unsafe URL path: {url!r}")
    return url


def http_host_allowlist(*, extra: frozenset[str] | set[str] | None = None) -> frozenset[str]:
    """Localhost defaults plus BLACKDARK_HTTP_HOST_ALLOWLIST (comma-separated)."""
    hosts = set(_DEFAULT_HTTP_HOSTS)
    if extra:
        hosts.update(h.strip().lower() for h in extra if str(h).strip())
    raw = os.getenv("BLACKDARK_HTTP_HOST_ALLOWLIST", "")
    for part in raw.split(","):
        host = part.strip().lower()
        if host:
            hosts.add(host)
    return frozenset(hosts)


def assert_safe_http_url(
    url: str,
    *,
    allowed_hosts: frozenset[str] | set[str] | None = None,
) -> str:
    """Allow only http/https to localhost/127.0.0.1 or a configured host allowlist."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"URL missing host: {url!r}")
    allow = http_host_allowlist(extra=allowed_hosts)
    if host not in allow:
        raise ValueError(f"Host not in allowlist: {host!r}")
    return url


def open_http_url(
    url: str,
    *,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    method: str | None = None,
    allowed_hosts: frozenset[str] | set[str] | None = None,
) -> Any:
    """
    Open http/https URLs only (rejects file:/ and custom schemes).

    When ``allowed_hosts`` is set, the URL hostname must be in that set.
    Centralizes urllib so call sites do not each trigger Bandit B310.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")
    host = (parsed.hostname or "").lower()
    if not host:
        raise ValueError(f"URL missing host: {url!r}")
    if allowed_hosts is not None:
        allow = {str(h).strip().lower() for h in allowed_hosts if str(h).strip()}
        if host not in allow:
            raise ValueError(f"Host not in allowlist: {host!r}")
    req = Request(url, data=data, headers=headers or {}, method=method)
    return urlopen(req, timeout=timeout)  # nosec B310


def safe_urlopen(
    url: str,
    *,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
    allowed_hosts: frozenset[str] | set[str] | None = None,
    data: bytes | None = None,
    method: str | None = None,
) -> Any:
    """Open URL after localhost/allowlist host checks (acceptance probes)."""
    safe_url = assert_safe_http_url(url, allowed_hosts=allowed_hosts)
    return open_http_url(
        safe_url,
        timeout=timeout,
        headers=headers,
        data=data,
        method=method,
        allowed_hosts=http_host_allowlist(extra=allowed_hosts),
    )


def validate_bind_host(host: str) -> str:
    """Validate a CLI bind/connect host before subprocess use."""
    cleaned = str(host).strip()
    if not cleaned or not _SAFE_HOST_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid host: {host!r}")
    if any(ch in cleaned for ch in (";", "|", "&", "$", "`", "\n", "\r", " ")):
        raise ValueError(f"Invalid host: {host!r}")
    return cleaned


def validate_port(port: int | str) -> int:
    """Validate a TCP port number."""
    try:
        value = int(port)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid port: {port!r}") from exc
    if not (1 <= value <= 65535):
        raise ValueError(f"Port out of range: {value}")
    return value


def project_data_dir(*, project_root: Path | str | None = None) -> Path:
    """Resolved `<project>/data` directory (never user-controlled)."""
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parent
    return (root / "data").resolve()


def safe_data_file(*parts: str, project_root: Path | str | None = None) -> Path:
    """
    Resolve a file under `<project>/data/...` with traversal rejection.
    Use at every durable write/read sink to satisfy path-injection gates (S2083).
    """
    if not parts:
        raise ValueError("safe_data_file requires at least one path part")
    for part in parts:
        cleaned = str(part).strip().replace("\\", "/")
        if not cleaned or cleaned in {".", ".."} or "/" in cleaned:
            raise ValueError(f"Unsafe data path part: {part!r}")
    return resolve_under(project_data_dir(project_root=project_root), *parts)
