"""TradingView Lightweight Charts config + webhook signal bridge."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.TradingViewBridge")


_LIGHTWEIGHT_CHARTS_V4_CDN = (
    "https://unpkg.com/lightweight-charts@4.2.0/dist/lightweight-charts.standalone.production.js"
)


def chart_config(symbol: str = "BTCUSDT") -> dict[str, Any]:
    return lightweight_charts_v4_config(symbol)


def lightweight_charts_v4_config(symbol: str = "BTCUSDT") -> dict[str, Any]:
    """#821 — TradingView Lightweight Charts v4 embed config."""
    return {
        "library": "TradingView Lightweight Charts",
        "version": "v4",
        "symbol": symbol,
        "note": "Pine Script is TradingView proprietary — use Lightweight Charts for embedded UI",
        "cdn": _LIGHTWEIGHT_CHARTS_V4_CDN,
        "theme": "dark",
        "layout": {
            "background": {"type": "solid", "color": "#0d1117"},
            "textColor": "#c9d1d9",
        },
        "grid": {"vertLines": {"color": "#21262d"}, "horzLines": {"color": "#21262d"}},
        "crosshair": {"mode": 1},
        "timeScale": {"borderColor": "#30363d", "timeVisible": True},
        "panes": {
            "main": {"type": "candlestick", "overlays": ["SMA(20)"]},
            "volume": {"type": "histogram", "height": 80},
            "rsi": {"type": "line", "period": 14, "height": 100},
            "macd": {"type": "macd", "params": "12,26,9", "height": 100},
        },
        "interaction": {"zoom": True, "pan": True, "handleScroll": True, "handleScale": True},
        "studies": ["volume", "rsi", "macd", "sma"],
        "max_candles": 50000,
        "responsive": True,
    }


async def handle_webhook(payload: dict[str, Any], *, signature: str | None = None) -> dict[str, Any]:
    secret = os.getenv("TRADINGVIEW_WEBHOOK_SECRET", "").strip()
    if secret and signature:
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return {"accepted": False, "reason": "invalid_signature"}

    action = str(payload.get("action") or payload.get("strategy", {}).get("order_action") or "").lower()
    symbol = str(payload.get("symbol") or payload.get("ticker") or "BTC").replace("USDT", "")
    if action in {"buy", "long", "enter_long"}:
        side = "buy"
    elif action in {"sell", "short"}:
        side = "sell"
    else:
        side = None

    if not side:
        return {"accepted": True, "executed": False, "reason": "no_trade_action", "payload": payload}

    from execution_engine import execute_order

    amount = float(payload.get("amount_usd") or os.getenv("TRADINGVIEW_DEFAULT_USD", "100"))
    result = await execute_order(symbol, side, amount, dry_run=True)
    return {
        "accepted": True,
        "executed": result.get("success", False),
        "dry_run": True,
        "order": result,
        "timestamp": datetime.now(UTC).isoformat(),
    }
