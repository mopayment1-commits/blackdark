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


def chart_config(symbol: str = "BTCUSDT") -> dict[str, Any]:
    return {
        "library": "TradingView Lightweight Charts",
        "symbol": symbol,
        "note": "Pine Script is TradingView proprietary — use Lightweight Charts for embedded UI",
        "cdn": "https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js",
        "theme": "dark",
        "studies": ["volume", "rsi"],
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
    side = "buy" if action in {"buy", "long", "enter_long"} else "sell" if action in {"sell", "short"} else None

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
