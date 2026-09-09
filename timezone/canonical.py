"""Canonical UTC instant handling — TZ-001, TZ-012, TZ-013, TZ-031."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def reject_naive(dt: datetime, *, context: str = "timestamp") -> None:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f"Naive {context} is not allowed in canonical paths")


def ensure_aware_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Naive datetime must be normalized explicitly before UTC conversion")
    return dt.astimezone(UTC)


def parse_iso(value: str | datetime | None) -> datetime:
    if value is None:
        raise ValueError("Missing timestamp")
    if isinstance(value, datetime):
        return ensure_aware_utc(value)
    raw = str(value).strip()
    if not raw:
        raise ValueError("Empty timestamp")
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        raise ValueError("Ambiguous timestamp without timezone")
    return dt.astimezone(UTC)


def format_api_timestamp(value: datetime | str | None) -> str:
    dt = parse_iso(value) if not isinstance(value, datetime) else ensure_aware_utc(value)
    text = dt.isoformat()
    if text.endswith("+00:00"):
        return text[:-6] + "Z"
    return text


def normalize_boundary(value: Any) -> datetime:
    if isinstance(value, datetime):
        return ensure_aware_utc(value)
    return parse_iso(str(value))
