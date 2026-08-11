"""
BLACKDARK — Hot tier read path for analytics / forecast modules.

When SQLite mirror is disabled (production default), modules read recent prices
from TimescaleDB or local NDJSON spool instead of pricing_logs.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.HotTierReader")


def _normalize_symbol(symbol: str) -> str:
    cleaned = symbol.upper().strip()
    if "/" not in cleaned and cleaned.endswith("USDT"):
        return f"{cleaned[:-4]}/USDT"
    return cleaned


def _price_from_ndjson_line(raw_line: str, symbol: str) -> float | None:
    stripped = raw_line.strip()
    if not stripped:
        return None
    try:
        row = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    if str(row.get("symbol", "")).upper() != symbol:
        return None
    payload = row.get("payload") or {}
    price = payload.get("price")
    return float(price) if price is not None else None


def _append_spool_prices(spool_file: Any, symbol: str, closes: list[float], limit: int) -> bool:
    try:
        with spool_file.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                price = _price_from_ndjson_line(raw_line, symbol)
                if price is not None:
                    closes.append(price)
                if len(closes) >= limit:
                    return True
    except OSError:
        return False
    return False


async def _read_timescale_closes(symbol: str, *, limit: int) -> list[float]:
    dsn = str(config.HOT_STORAGE_TIMESCALE_DSN or "").strip()
    if not dsn:
        return []
    try:
        import asyncpg
    except ImportError:
        return []

    schema = config.HOT_STORAGE_TIMESCALE_SCHEMA
    sym = _normalize_symbol(symbol)
    try:
        conn = await asyncpg.connect(dsn=dsn, timeout=8)
        try:
            rows = await conn.fetch(
                f"""
                SELECT price
                FROM {schema}.hot_pricing
                WHERE symbol = $1
                ORDER BY timestamp DESC
                LIMIT $2
                """,
                sym,
                limit,
            )
        finally:
            await conn.close()
        return [float(row["price"]) for row in reversed(rows) if row["price"] is not None]
    except Exception:
        logger.debug("Timescale hot-tier read failed | symbol=%s", sym, exc_info=True)
        return []


def _read_ndjson_closes(symbol: str, *, limit: int) -> list[float]:
    sym = _normalize_symbol(symbol)
    root = config.HOT_STORAGE_DIR / "pricing"
    if not root.is_dir():
        return []

    closes: list[float] = []
    files = sorted(root.glob("*.ndjson"), reverse=True)
    for spool_file in files:
        if _append_spool_prices(spool_file, sym, closes, limit):
            return closes[-limit:]
    return closes[-limit:]


async def fetch_recent_closes(
    symbol: str,
    *,
    limit: int = 200,
) -> tuple[list[float], str]:
    """Load recent close prices from hot tier backends."""
    sym = _normalize_symbol(symbol)

    ts_closes = await _read_timescale_closes(sym, limit=limit)
    if len(ts_closes) >= 24:
        return ts_closes, "hot_timescale"

    ndjson_closes = _read_ndjson_closes(sym, limit=limit)
    if len(ndjson_closes) >= 24:
        return ndjson_closes, "hot_ndjson_spool"

    from database import fetch_recent_pricing_for_symbol

    local_rows = await fetch_recent_pricing_for_symbol(sym, limit=limit)
    if len(local_rows) >= 24:
        closes = [float(r["price"]) for r in reversed(local_rows)]
        return closes, "legacy_sqlite_pricing_logs"

    return [], "none"


def hot_tier_status() -> dict[str, Any]:
    root = config.HOT_STORAGE_DIR
    spool_files = 0
    spool_bytes = 0
    if root.exists():
        for path in root.rglob("*.ndjson"):
            spool_files += 1
            try:
                spool_bytes += path.stat().st_size
            except OSError:
                pass
    return {
        "backend": config.HOT_STORAGE_BACKEND,
        "retention_hours": config.HOT_TIER_RETENTION_HOURS,
        "mirror_sqlite": config.HOT_STORAGE_MIRROR_SQLITE,
        "timescale_configured": bool(config.HOT_STORAGE_TIMESCALE_DSN),
        "clickhouse_configured": bool(config.HOT_STORAGE_CLICKHOUSE_URL),
        "ndjson_files": spool_files,
        "ndjson_mb": round(spool_bytes / (1024 * 1024), 2),
        "last_checked": datetime.now(UTC).isoformat(),
    }
