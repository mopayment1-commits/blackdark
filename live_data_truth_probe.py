"""Live data-truth probe — prove public market ingestion + canonical adoption.

Uses Binance public REST (no credentials). Fail-closed when network/unavailable.
Never invents LIVE quotes.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any


async def probe_binance_public_book(symbol: str = "BTCUSDT") -> dict[str, Any]:
    """Fetch live top-of-book from Binance public API and adopt canonically."""
    import httpx

    from canonical_adoption import adopt_tick_quote
    from canonical_data_layer import EntityType, FreshnessClass, get_datum, reset_store_for_tests

    # Do not wipe global store in production — only isolate on explicit test flag.
    url = f"https://api.binance.com/api/v3/ticker/bookTicker?symbol={symbol}"
    started = time.time()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url)
            latency_ms = int((time.time() - started) * 1000)
            if r.status_code != 200:
                return {
                    "ok": False,
                    "live": False,
                    "reason": f"http_{r.status_code}",
                    "latency_ms": latency_ms,
                    "executable_quotes": False,
                }
            data = r.json()
            bid = float(data["bidPrice"])
            ask = float(data["askPrice"])
            provider_ts_ms = int(time.time() * 1000)
            adopted = adopt_tick_quote(
                venue="binance",
                symbol=symbol if "/" in symbol else f"{symbol[:-4]}/{symbol[-4:]}",
                bid=bid,
                ask=ask,
                source="binance_public_bookticker",
                provider_timestamp=provider_ts_ms,
                bid_qty=float(data.get("bidQty") or 0) or None,
                ask_qty=float(data.get("askQty") or 0) or None,
                require_live=True,
                path="streaming",
            )
            datum = get_datum(EntityType.QUOTE, f"{adopted['venue']}:{adopted['symbol']}")
            freshness = adopted.get("freshness_class")
            live = freshness == FreshnessClass.LIVE.value
            return {
                "ok": True,
                "live": live,
                "venue": adopted["venue"],
                "symbol": adopted["symbol"],
                "bid": bid,
                "ask": ask,
                "freshness_class": freshness,
                "executable_quotes": live,
                "latency_ms": latency_ms,
                "canonical_id": datum.id if datum else None,
                "source": "binance_public_bookticker",
                "probed_at": datetime.now(UTC).isoformat(),
            }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "live": False,
            "reason": f"network_unavailable:{type(exc).__name__}",
            "executable_quotes": False,
            "probed_at": datetime.now(UTC).isoformat(),
        }


def probe_status() -> dict[str, Any]:
    return {
        "surface": "live_data_truth_probe",
        "provider": "binance_public_rest",
        "credentials_required": False,
        "fail_closed_on_outage": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "note": "Proves live public book → canonical adopt when network available.",
    }
