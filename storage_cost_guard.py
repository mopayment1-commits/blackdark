"""
BLACKDARK — Storage cost guard (anti data-bloat / cloud cost protection).

Prevents terabyte-scale hot-tier growth at 100-exchange scale:
- Per-record-type archival toggles (ticks/order books off by default)
- Global symbol throttle (pricing 1 Hz default)
- Daily write budget (MB cap)
- Cost/status reporting for SaaS margin protection
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.StorageCostGuard")

_last_write_mono: dict[str, float] = {}
_skipped_by_type: dict[str, int] = {}
_throttled_total = 0
_skipped_total = 0
_daily_bytes = 0
_daily_day: str = ""


def _enabled() -> bool:
    return getattr(config, "STORAGE_COST_GUARD_ENABLED", True)


def _utc_day() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _reset_daily_if_needed() -> None:
    global _daily_bytes, _daily_day
    day = _utc_day()
    if day != _daily_day:
        _daily_day = day
        _daily_bytes = 0


def _record_key(record_type: str, exchange: str, symbol: str) -> str:
    return f"{record_type}|{exchange.lower()}|{symbol.upper()}"


def throttle_ms_for(record_type: str) -> int:
    if record_type == "tick":
        return int(getattr(config, "HOT_STORAGE_TICK_THROTTLE_MS", 0))
    if record_type == "order_book":
        return int(getattr(config, "HOT_STORAGE_ORDER_BOOK_THROTTLE_MS", 60_000))
    if record_type == "funding":
        return int(getattr(config, "HOT_STORAGE_FUNDING_THROTTLE_MS", 60_000))
    return int(getattr(config, "HOT_STORAGE_SYMBOL_THROTTLE_MS", 1000))


def should_archive_record_type(record_type: str) -> bool:
    if not _enabled():
        return True
    mapping = {
        "pricing": getattr(config, "HOT_STORAGE_ARCHIVE_PRICING", True),
        "order_book": getattr(config, "HOT_STORAGE_ARCHIVE_ORDER_BOOKS", False),
        "tick": getattr(config, "HOT_STORAGE_ARCHIVE_TICKS", False),
        "funding": getattr(config, "HOT_STORAGE_ARCHIVE_FUNDING", True),
    }
    return bool(mapping.get(record_type, True))


def _estimate_payload_bytes(record_type: str, payload: dict[str, Any] | None) -> int:
    if not payload:
        return 128
    if record_type == "order_book":
        try:
            return len(json.dumps(payload, separators=(",", ":")))
        except (TypeError, ValueError):
            return 4096
    if record_type == "tick":
        return 160
    return 200


def check_and_record_write(
    record_type: str,
    exchange: str,
    symbol: str,
    *,
    payload: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    """
    Return (allowed, reason). Updates throttle timestamps and daily byte budget on allow.
    """
    global _throttled_total, _skipped_total, _daily_bytes

    if not _enabled():
        return True, "guard_disabled"

    if not should_archive_record_type(record_type):
        _skipped_total += 1
        _skipped_by_type[record_type] = _skipped_by_type.get(record_type, 0) + 1
        return False, f"record_type_disabled:{record_type}"

    throttle_ms = throttle_ms_for(record_type)
    if throttle_ms > 0:
        key = _record_key(record_type, exchange, symbol)
        now = time.monotonic()
        last = _last_write_mono.get(key, 0.0)
        if (now - last) * 1000.0 < throttle_ms:
            _throttled_total += 1
            return False, "throttled"
        _last_write_mono[key] = now

    _reset_daily_if_needed()
    est_bytes = _estimate_payload_bytes(record_type, payload)
    daily_cap_mb = float(getattr(config, "HOT_STORAGE_DAILY_MAX_MB", 2048))
    daily_cap_bytes = int(daily_cap_mb * 1024 * 1024)
    if daily_cap_bytes > 0 and (_daily_bytes + est_bytes) > daily_cap_bytes:
        _skipped_total += 1
        _skipped_by_type["daily_budget"] = _skipped_by_type.get("daily_budget", 0) + 1
        logger.warning(
            "Hot storage daily budget exceeded | day=%s bytes=%d cap_mb=%.0f",
            _daily_day,
            _daily_bytes,
            daily_cap_mb,
        )
        return False, "daily_budget_exceeded"

    _daily_bytes += est_bytes
    return True, "ok"


def estimate_weekly_hot_gb() -> dict[str, Any]:
    """Conservative upper-bound estimate from active config (not live counters)."""
    throttle_pricing = max(1, throttle_ms_for("pricing"))
    pricing_rows_day = (
        (86_400_000 / throttle_pricing)
        * (25 if getattr(config, "HOT_STORAGE_ARCHIVE_PRICING", True) else 0)
    )
    ob_rows_day = (
        (86_400_000 / max(1, throttle_ms_for("order_book")))
        * (25 if getattr(config, "HOT_STORAGE_ARCHIVE_ORDER_BOOKS", False) else 0)
    )
    tick_rows_day = (
        (86_400_000 / max(1, throttle_ms_for("tick") or 1))
        * (10 if getattr(config, "HOT_STORAGE_ARCHIVE_TICKS", False) else 0)
    )
    bytes_day = pricing_rows_day * 200 + ob_rows_day * 4096 + tick_rows_day * 160
    gb_week = round(bytes_day * 7 / (1024**3), 2)
    return {
        "estimated_hot_gb_per_week": gb_week,
        "pricing_archived": getattr(config, "HOT_STORAGE_ARCHIVE_PRICING", True),
        "order_books_archived": getattr(config, "HOT_STORAGE_ARCHIVE_ORDER_BOOKS", False),
        "ticks_archived": getattr(config, "HOT_STORAGE_ARCHIVE_TICKS", False),
        "daily_max_mb": float(getattr(config, "HOT_STORAGE_DAILY_MAX_MB", 2048)),
        "note": "Estimate assumes single-writer pricing throttle; REST scale uses ingress caps.",
    }


def storage_cost_guard_status() -> dict[str, Any]:
    _reset_daily_if_needed()
    daily_cap_mb = float(getattr(config, "HOT_STORAGE_DAILY_MAX_MB", 2048))
    return {
        "enabled": _enabled(),
        "archive_pricing": getattr(config, "HOT_STORAGE_ARCHIVE_PRICING", True),
        "archive_order_books": getattr(config, "HOT_STORAGE_ARCHIVE_ORDER_BOOKS", False),
        "archive_ticks": getattr(config, "HOT_STORAGE_ARCHIVE_TICKS", False),
        "archive_funding": getattr(config, "HOT_STORAGE_ARCHIVE_FUNDING", True),
        "pricing_throttle_ms": throttle_ms_for("pricing"),
        "order_book_throttle_ms": throttle_ms_for("order_book"),
        "tick_throttle_ms": throttle_ms_for("tick"),
        "daily_max_mb": daily_cap_mb,
        "daily_bytes_written": _daily_bytes,
        "daily_mb_used": round(_daily_bytes / (1024 * 1024), 2),
        "daily_budget_pct": round(
            (_daily_bytes / max(1, int(daily_cap_mb * 1024 * 1024))) * 100, 2
        ),
        "throttled_total": _throttled_total,
        "skipped_total": _skipped_total,
        "skipped_by_type": dict(_skipped_by_type),
        "weekly_estimate": estimate_weekly_hot_gb(),
        "ai_training_note": (
            "ML/oracle training uses labeled oracle rows in SQLite/Parquet — "
            "NOT raw tick spool. Disabling tick/order-book archival does not block AI."
        ),
        "policy": (
            "Default: pricing 1 Hz only; order books + raw ticks not archived. "
            "Enable HOT_STORAGE_ARCHIVE_ORDER_BOOKS/TICKS only for research exports."
        ),
    }
