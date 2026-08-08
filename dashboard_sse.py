"""
BLACKDARK — Dashboard SSE live feed (market, arb, whales).

Powers no-refresh UI updates on /dashboard via EventSource.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _dashboard_snapshot() -> dict[str, Any]:
    payload: dict[str, Any] = {"type": "dashboard", "timestamp": _utcnow()}

    try:
        from market_context import fetch_binance_market_overview, fetch_cvvd_whale_context

        assets = await fetch_binance_market_overview()
        payload["market"] = {"assets": assets[:8], "count": len(assets)}

        ctx = await fetch_cvvd_whale_context(refresh=False)
        alerts = ctx.get("whale_alerts") or []
        payload["whales"] = {"alerts": alerts[:8], "count": len(alerts)}
    except Exception:
        payload["market"] = {"assets": [], "count": 0}
        payload["whales"] = {"alerts": [], "count": 0}

    try:
        from scan_coordinator import get_shared_scan

        scan = await get_shared_scan(profitable_only=False, prefer_live=True)
        opps = scan.get("opportunities") or []
        payload["arbitrage"] = {
            "opportunities": opps[:6],
            "counts": scan.get("counts") or {},
            "profitable_count": scan.get("profitable_count", 0),
            "executable_count": scan.get("executable_count", 0),
        }
    except Exception:
        payload["arbitrage"] = {"opportunities": [], "counts": {}}

    try:
        from market_intel import fetch_open_interest

        oi = await fetch_open_interest()
        payload["open_interest"] = {"assets": (oi or [])[:6]}
    except Exception:
        payload["open_interest"] = {"assets": []}

    return payload


async def dashboard_sse_generator(*, interval_sec: float = 15.0) -> AsyncIterator[str]:
    yield f"data: {json.dumps({'type': 'connected', 'timestamp': _utcnow()})}\n\n"
    while True:
        try:
            snap = await _dashboard_snapshot()
            yield f"data: {json.dumps(snap, default=str)}\n\n"
        except asyncio.CancelledError:
            break
        except Exception as exc:
            err = {"type": "error", "message": str(exc), "timestamp": _utcnow()}
            yield f"data: {json.dumps(err)}\n\n"
        await asyncio.sleep(interval_sec)
