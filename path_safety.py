"""Shared path / URL safety helpers for Sonar path-injection and SSRF rules."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from collections.abc import Iterable, Sequence
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


def coerce_json_value(raw: object) -> object:
    """Deep-copy a JSON value with runtime type validation (S2083 content sanitizer)."""
    if raw is None or isinstance(raw, bool):
        return raw
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return raw
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return [coerce_json_value(item) for item in raw]
    if isinstance(raw, dict):
        return coerce_json_mapping(raw)
    raise ValueError(f"Unsupported JSON value type: {type(raw).__name__}")


def coerce_json_mapping(raw: object) -> dict[str, object]:
    """Return a fresh JSON object with only JSON-safe primitive/container values."""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, object] = {}
    for key, value in raw.items():
        if not isinstance(key, str):
            continue
        out[key] = coerce_json_value(value)
    return out


def read_json_mapping(path: Path) -> dict[str, object]:
    """Read JSON from a resolved path and return a sanitized mapping."""
    parsed = json.loads(path.read_text(encoding="utf-8"))
    return coerce_json_mapping(parsed)


def write_json_mapping(path: Path, document: dict[str, object]) -> None:
    """Write a sanitized JSON mapping to a resolved path."""
    write_json_artifact(path, coerce_json_mapping(document), base=project_root_dir())


def project_root_dir(*, project_root: Path | str | None = None) -> Path:
    """Resolved repository root (directory containing path_safety.py)."""
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parent


def resolve_project_file(*parts: str, project_root: Path | str | None = None) -> Path:
    """Resolve a path under the repository root; reject traversal in parts."""
    root = project_root_dir(project_root=project_root)
    for part in parts:
        cleaned = str(part).strip().replace("\\", "/")
        if not cleaned or cleaned in {".", ".."} or "/" in cleaned:
            raise ValueError(f"Unsafe project path part: {part!r}")
    return resolve_under(root, *parts)


_PUBLIC_ARTIFACT_SUFFIXES = frozenset({".json", ".jsonl", ".md", ".txt", ".csv", ".log"})
_SECRET_PATH_SEGMENT_RE = re.compile(
    r"(^|/)(secrets?|vault|credentials?|passwords?|private[-_]?keys?|\.env)(/|$)",
    re.IGNORECASE,
)


def _resolve_public_artifact_path(path: Path, base: Path | str) -> Path:
    """Artifact destinations only — never under secret/vault/credential paths (S2083 + CWE-312)."""
    base_resolved = Path(base).resolve()
    bounded = ensure_under(Path(path).resolve(), base_resolved)
    rel_parts = bounded.relative_to(base_resolved).parts
    if not rel_parts:
        raise ValueError("Refusing to write repository root path")
    dest = resolve_under(base_resolved, *rel_parts)
    rel_posix = dest.relative_to(base_resolved).as_posix()
    if _SECRET_PATH_SEGMENT_RE.search(rel_posix):
        raise ValueError(f"Refusing artifact write under secret-class path: {dest}")
    suffix = dest.suffix.lower()
    if suffix and suffix not in _PUBLIC_ARTIFACT_SUFFIXES:
        raise ValueError(f"Unsupported public artifact extension: {suffix!r}")
    return dest


def _write_public_artifact_bytes(dest: Path, payload: bytes) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as handle:
        handle.write(payload)


def write_json_artifact(path: Path, document: object, *, base: Path | str) -> None:
    """Write JSON-safe artifact data (coerced — not raw secrets)."""
    dest = _resolve_public_artifact_path(path, base)
    safe = coerce_json_value(document)
    data = (json.dumps(safe, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _write_public_artifact_bytes(dest, data)


def write_public_text_lines(path: Path, lines: Sequence[str], *, base: Path | str) -> None:
    """Write markdown/text closure artifacts from discrete lines (no secret-store paths)."""
    dest = _resolve_public_artifact_path(path, base)
    if dest.suffix.lower() not in {".md", ".txt", ".jsonl", ".log", ".csv", ""}:
        raise ValueError(f"Prose artifacts must use .md/.txt/.jsonl/.log/.csv: {dest}")
    body = "\n".join(lines)
    if body and not body.endswith("\n"):
        body += "\n"
    _write_public_artifact_bytes(dest, body.encode("utf-8"))


def write_jsonl_artifact(path: Path, rows: Iterable[object], *, base: Path | str) -> None:
    """Append-safe JSONL artifact write from JSON-safe rows."""
    dest = _resolve_public_artifact_path(path, base)
    chunks: list[bytes] = []
    for row in rows:
        if not row:
            continue
        safe = coerce_json_value(row)
        chunks.append((json.dumps(safe, default=str) + "\n").encode("utf-8"))
    _write_public_artifact_bytes(dest, b"".join(chunks))


def write_utf8_bound(path: Path, content: str, *, base: Path | str) -> None:
    """Backward-compatible prose artifact write (delegates to line-based public writer)."""
    write_public_text_lines(path, content.splitlines(), base=base)


def write_json_at_data(*parts: str, value: object, project_root: Path | str | None = None) -> Path:
    """Serialize JSON under ``<project>/data/...`` using literal path parts only."""
    target = safe_data_file(*parts, project_root=project_root)
    write_json_artifact(target, value, base=project_data_dir(project_root=project_root))
    return target


_BACKUP_BASENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def backup_data_dir(*, project_root: Path | str | None = None) -> Path:
    """Resolved ``<project>/data/backups`` directory."""
    return resolve_under(project_data_dir(project_root=project_root), "backups")


def resolve_backup_store_dir(*, project_root: Path | str | None = None) -> Path:
    """Backup directory bound to project ``data/backups`` (ignores hostile BACKUP_DIR)."""
    root = project_root_dir(project_root=project_root)
    raw = os.getenv("BACKUP_DIR", "data/backups").strip()
    if raw in {"", "data/backups", "backups"}:
        return backup_data_dir(project_root=root)
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = (root / raw).resolve()
    return ensure_under(candidate, root)


def resolve_backup_file(
    basename: str,
    *,
    store: Path | None = None,
    project_root: Path | str | None = None,
) -> Path:
    """Map an evidence basename to a file under the bounded backup store."""
    name = Path(str(basename)).name
    if not name or not _BACKUP_BASENAME_RE.fullmatch(name):
        raise ValueError(f"Unsafe backup basename: {basename!r}")
    base = store if store is not None else resolve_backup_store_dir(project_root=project_root)
    root = project_root_dir(project_root=project_root)
    return ensure_under((base / name).resolve(), root)
