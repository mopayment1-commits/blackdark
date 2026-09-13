"""
BLACKDARK canonical time & timezone utilities (TZ SSOT v1).

UTC is canonical for storage/transport/ordering. User IANA zones are for display only.
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, available_timezones

logger = logging.getLogger("BLACKDARK.Timezone")

_AUDIT_LOCK = threading.Lock()
_AUDIT_PATH = Path(__file__).resolve().parents[1] / "data" / "timezone_preference_audit.jsonl"

_ISO_Z_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)


class TimePolicyViolation(ValueError):
    """Fail-closed rejection for naive/invalid authoritative timestamps."""


class DstResolution(str, Enum):
    """TZ-026 deterministic fold/gap behavior."""

    EARLIER = "earlier"  # ambiguous local → earlier UTC instant
    LATER = "later"  # ambiguous local → later UTC instant
    REJECT_GAP = "reject_gap"  # nonexistent local → raise


def time_enforce_enabled() -> bool:
    """TZ-031 / T7 — default ON; production cannot disable."""
    raw = (os.getenv("BLACKDARK_TIME_ENFORCE", "1") or "1").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        try:
            from production_guard import is_production

            if is_production():
                return True
        except Exception:
            pass
        return False
    return True


def utc_now() -> datetime:
    """TZ-001 — timezone-aware UTC instant."""
    return datetime.now(UTC)


def utc_now_iso() -> str:
    """TZ-001 / TZ-013 — canonical UTC ISO-8601 with offset."""
    return format_iso_z(utc_now())


def format_iso_z(dt: datetime) -> str:
    """TZ-013 — unambiguous ISO-8601/RFC3339 with Z or offset."""
    if dt.tzinfo is None:
        if time_enforce_enabled():
            raise TimePolicyViolation("naive_datetime_forbidden_for_iso_export")
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")


def ensure_aware_utc(dt: datetime, *, field: str = "timestamp") -> datetime:
    """TZ-031 — reject naive datetimes at trust boundaries when enforcement ON."""
    if dt.tzinfo is None:
        if time_enforce_enabled():
            raise TimePolicyViolation(f"naive_{field}_rejected")
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_to_utc(value: str | int | float | datetime | None) -> datetime | None:
    """Parse common inputs to UTC-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return ensure_aware_utc(value)
    if isinstance(value, (int, float)):
        # Epoch seconds (not ms) — contract documented in tests
        if value > 1e12:
            value = value / 1000.0
        return datetime.fromtimestamp(float(value), tz=UTC)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return ensure_aware_utc(datetime.fromisoformat(text))


def validate_iana_timezone(tz_name: str) -> bool:
    """TZ-002 / TZ-032 — IANA TZDB identifier validation."""
    if not tz_name or tz_name.upper() == "UTC":
        return tz_name == "UTC" or tz_name == "Etc/UTC"
    return tz_name in available_timezones()


def safe_timezone(tz_name: str | None) -> str:
    """TZ-033 — fallback to UTC for invalid zones."""
    name = (tz_name or "UTC").strip()
    if name.upper() == "UTC":
        return "UTC"
    if validate_iana_timezone(name):
        return name
    logger.warning("timezone_invalid_fallback", extra={"requested": name, "fallback": "UTC"})
    return "UTC"


def resolve_timezone(
    *,
    request_override: str | None = None,
    account_preference: str | None = None,
    session_preference: str | None = None,
    detected_browser: str | None = None,
) -> str:
    """TZ-004 preference precedence chain."""
    for candidate in (
        request_override,
        account_preference,
        session_preference,
        detected_browser,
    ):
        if candidate and str(candidate).strip():
            return safe_timezone(str(candidate).strip())
    return "UTC"


def to_display_tz(dt: datetime, tz_name: str) -> datetime:
    """TZ-008 / TZ-014 — DST-aware display conversion."""
    aware = ensure_aware_utc(dt)
    zone = ZoneInfo(safe_timezone(tz_name))
    return aware.astimezone(zone)


def _local_wall_time_exists(naive: datetime, zone: ZoneInfo) -> bool:
    """Detect spring-forward gap: two folds round-trip locally but o1 > o0 (DST jump)."""
    offsets: list[Any] = []
    for fold in (0, 1):
        dt = datetime(
            naive.year,
            naive.month,
            naive.day,
            naive.hour,
            naive.minute,
            naive.second,
            naive.microsecond,
            tzinfo=zone,
            fold=fold,
        )
        if dt.astimezone(zone).replace(tzinfo=None) == naive:
            offsets.append(dt.utcoffset())
    if len(offsets) < 2:
        return bool(offsets)
    # Spring-forward gap: later fold has strictly greater UTC offset.
    return offsets[1] <= offsets[0]


def resolve_local_to_utc(
    local_dt: datetime,
    tz_name: str,
    *,
    dst: DstResolution = DstResolution.EARLIER,
) -> datetime:
    """TZ-026 — deterministic ambiguous/nonexistent local time handling."""
    zone = ZoneInfo(safe_timezone(tz_name))
    naive = local_dt.replace(tzinfo=None) if local_dt.tzinfo else local_dt
    if dst == DstResolution.REJECT_GAP and not _local_wall_time_exists(naive, zone):
        raise TimePolicyViolation(f"nonexistent_local_time:{tz_name}")
    fold = 0 if dst == DstResolution.EARLIER else 1
    try:
        return datetime(
            naive.year,
            naive.month,
            naive.day,
            naive.hour,
            naive.minute,
            naive.second,
            naive.microsecond,
            tzinfo=zone,
            fold=fold,
        ).astimezone(UTC)
    except Exception as exc:
        if dst == DstResolution.REJECT_GAP:
            raise TimePolicyViolation(f"nonexistent_local_time:{tz_name}") from exc
        raise TimePolicyViolation(f"unresolved_local_time:{tz_name}") from exc


def audit_timezone_change(
    *,
    user_id: str | int,
    old_tz: str | None,
    new_tz: str,
    source: str,
) -> dict[str, Any]:
    """TZ-028 — material preference change audit record (UTC canonical)."""
    return {
        "event": "timezone_preference_change",
        "user_id": str(user_id),
        "old_timezone": old_tz or "UTC",
        "new_timezone": safe_timezone(new_tz),
        "source": source,
        "recorded_at": utc_now_iso(),
    }


def persist_timezone_audit(record: dict[str, Any], *, audit_path: Path | None = None) -> dict[str, Any]:
    """Append TZ-028 audit row to JSONL ledger."""
    path = audit_path or _AUDIT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(record)
    row.setdefault("recorded_at", utc_now_iso())
    with _AUDIT_LOCK:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row


def timezone_status() -> dict[str, Any]:
    sample = "America/New_York"
    now = utc_now()
    local = to_display_tz(now, sample)
    return {
        "canonical_storage": "UTC",
        "enforce_enabled": time_enforce_enabled(),
        "iana_available": True,
        "sample_zone": sample,
        "sample_utc": format_iso_z(now),
        "sample_local": format_iso_z(local),
        "dst_aware": local.dst() is not None,
        "supported_zones_count": len(available_timezones()),
    }
