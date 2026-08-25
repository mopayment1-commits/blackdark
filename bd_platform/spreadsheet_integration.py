"""
Spreadsheet Integration — Features #174 + #176 (Wave 3, merged).

Google Sheets first: =BLACKDARK(ticker, metric, [exchange])

Cell-friendly responses with error parity:
  #ERROR: Rate limit
  #N/A: Invalid symbol

Auth parity with Unified API Platform (#162).
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.SpreadsheetIntegration")

_FEATURE_IDS = (174, 176)
_FUNCTION_NAME = "BLACKDARK"
_VALID_METRICS = frozenset({
    "price", "change_24h", "funding_rate", "sentiment", "liquidity_score",
    "oracle_verdict", "exit_zone_low", "exit_zone_high",
})


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _cell_error(code: str, detail: str = "") -> dict[str, Any]:
    msg = f"#ERROR: {code}" if not detail else f"#ERROR: {code} — {detail}"
    return {
        "ok": False,
        "cell_value": msg,
        "error_code": code,
        "spreadsheet_function": f"={_FUNCTION_NAME}()",
    }


def _cell_na(reason: str = "Invalid symbol") -> dict[str, Any]:
    return {
        "ok": False,
        "cell_value": f"#N/A: {reason}",
        "error_code": "invalid_symbol",
    }


async def evaluate_blackdark_function(
    ticker: str,
    metric: str,
    exchange: str | None = None,
    *,
    client_key: str = "sheets_default",
) -> dict[str, Any]:
    """
    Evaluate =BLACKDARK(ticker, metric, [exchange]) for Google Sheets / Excel.

    Returns cell_value suitable for direct paste into spreadsheet cell.
    """
    t0 = time.perf_counter()
    sym = (ticker or "").strip().upper().replace("/USDT", "")
    met = (metric or "").strip().lower()

    if not sym or len(sym) > 12 or not sym.isalnum():
        return _cell_na("Invalid symbol")

    if met not in _VALID_METRICS:
        return _cell_na(f"Unknown metric '{metric}'")

    from bd_platform.unified_api_platform import check_api_rate_limit

    blocked = check_api_rate_limit(f"sheets:{client_key}")
    if blocked:
        return _cell_error("Rate limit", "retry in 60s")

    try:
        cell_value: str | float | None = None

        if met == "price":
            from bd_platform.unified_api_platform import fetch_price

            resp = await fetch_price(sym, exchange=exchange)
            cell_value = (resp.get("data") or {}).get("price_usd")
        elif met == "change_24h":
            from bd_platform.unified_api_platform import fetch_price

            resp = await fetch_price(sym, exchange=exchange)
            cell_value = (resp.get("data") or {}).get("change_24h_pct")
        elif met == "funding_rate":
            from bd_platform.free_market_data import binance_futures_snapshot

            snap = await binance_futures_snapshot(sym)
            cell_value = snap.get("funding_rate_pct")
        elif met == "sentiment":
            from bd_platform.unified_api_platform import fetch_sentiment

            resp = await fetch_sentiment(sym)
            cell_value = (resp.get("data") or {}).get("weighted_sentiment_score")
        elif met == "liquidity_score":
            from bd_platform.unified_api_platform import fetch_liquidity

            resp = await fetch_liquidity(sym)
            cell_value = (resp.get("data") or {}).get("health_score")
        elif met == "oracle_verdict":
            from bd_platform.unified_api_platform import fetch_oracle

            resp = await fetch_oracle(sym)
            cell_value = (resp.get("data") or {}).get("verdict")
        elif met in {"exit_zone_low", "exit_zone_high"}:
            from bd_platform.unified_api_platform import fetch_exit_zone

            resp = await fetch_exit_zone(sym)
            zone = (resp.get("data") or {}).get("exit_zone") or {}
            cell_value = zone.get("low_usd") if met == "exit_zone_low" else zone.get("high_usd")

        if cell_value is None:
            return _cell_na("No data")

        elapsed = (time.perf_counter() - t0) * 1000
        return {
            "ok": True,
            "feature_ids": list(_FEATURE_IDS),
            "function": f"={_FUNCTION_NAME}({ticker}, {metric})",
            "ticker": sym,
            "metric": met,
            "exchange": exchange,
            "cell_value": cell_value,
            "api_parity": True,
            "auth": "api_key_or_oauth",
            "sla_met": elapsed <= 2000,
            "latency_ms": round(elapsed, 1),
            "timestamp": _utcnow(),
        }
    except Exception as exc:
        logger.debug("sheet function failed", exc_info=True)
        return _cell_error("Internal", str(exc)[:80])


def spreadsheet_integration_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_ids": list(_FEATURE_IDS),
        "title": "Spreadsheet Integration",
        "primary_target": "google_sheets",
        "function_syntax": f"={_FUNCTION_NAME}(ticker, metric, [exchange])",
        "valid_metrics": sorted(_VALID_METRICS),
        "error_formats": ["#ERROR: Rate limit", "#N/A: Invalid symbol"],
        "auth": "Google OAuth + API key parity with #162",
        "integrated_features": ["#162"],
        "timestamp": _utcnow(),
    }
