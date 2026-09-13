"""Vendor API rate-limit watchdog — surfaces throttling before users complain."""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from typing import Any


def vendor_rate_limit_status() -> dict[str, Any]:
    """Aggregate outbound vendor throttle signals (CoinGecko, exchanges, LLM)."""
    signals: list[dict[str, Any]] = []
    overall_ok = True

    try:
        from blackdark.ingestion.coingecko_connector import coingecko_connector_status

        cg = coingecko_connector_status()
        limited_until = cg.get("rate_limited_until")
        if limited_until:
            remaining = max(0.0, float(limited_until) - time.time())
            signals.append(
                {
                    "vendor": "coingecko",
                    "throttled": True,
                    "remaining_sec": round(remaining, 1),
                    "api_key_configured": cg.get("api_key_configured"),
                    "cache_entries": cg.get("cache_entries"),
                }
            )
            overall_ok = False
        else:
            signals.append({"vendor": "coingecko", "throttled": False, "api_key_configured": cg.get("api_key_configured")})
    except Exception as exc:
        signals.append({"vendor": "coingecko", "error": type(exc).__name__})

    try:
        from exchange_ingress_guard import ingress_guard_status

        ig = ingress_guard_status()
        banned = ig.get("banned_exchanges") or {}
        if banned:
            signals.append({"vendor": "exchange_ingress", "throttled": True, "banned_exchanges": banned})
            overall_ok = False
        else:
            strikes = {k: v for k, v in (ig.get("error_strikes") or {}).items() if int(v) >= 3}
            if strikes:
                signals.append({"vendor": "exchange_ingress", "throttled": False, "high_error_strikes": strikes})
            else:
                signals.append({"vendor": "exchange_ingress", "throttled": False})
    except Exception as exc:
        signals.append({"vendor": "exchange_ingress", "error": type(exc).__name__})

    projected = int(os.getenv("LAUNCH_PROJECTED_USERS", "100"))
    return {
        "checked_at": datetime.now(UTC).isoformat(),
        "overall_ok": overall_ok,
        "signals": signals,
        "projected_users": projected,
        "upgrade_recommended": projected >= 50 and not _coingecko_pro_configured(),
        "audit_artifact": "FREE_API_RATE_LIMIT_AUDIT.json",
    }


def _coingecko_pro_configured() -> bool:
    return bool(os.getenv("COINGECKO_API_KEY", "").strip() or os.getenv("COINMARKETCAP_API_KEY", "").strip())


def should_alert_vendor_throttle() -> tuple[bool, str | None]:
    status = vendor_rate_limit_status()
    if not status.get("overall_ok"):
        throttled = [s for s in status.get("signals", []) if s.get("throttled")]
        return True, f"vendor_throttle:{','.join(s['vendor'] for s in throttled)}"
    return False, None
