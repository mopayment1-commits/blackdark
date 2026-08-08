"""Server-Sent Events live feed for opportunities and platform stats."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


async def _snapshot_event() -> dict:
    payload: dict = {"timestamp": _utcnow(), "type": "heartbeat"}
    try:
        from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities

        cex_dex = await scan_cex_dex_opportunities(quote_usd=500)
        payload["cex_dex_count"] = cex_dex.get("count", 0)
        payload["cex_dex_top"] = cex_dex.get("top")
    except Exception:
        payload["cex_dex_count"] = 0

    try:
        from arbitrage_engine import scan_all_opportunities

        arb = await scan_all_opportunities(limit=5)
        payload["arb_count"] = len(arb.get("opportunities") or [])
        payload["arb_top"] = (arb.get("opportunities") or [None])[0]
    except Exception:
        payload["arb_count"] = 0

    try:
        from bd_platform.drawdown_guard import drawdown_status

        payload["drawdown"] = drawdown_status()
    except Exception:
        pass

    payload["type"] = "snapshot"
    return payload


async def sse_event_generator(*, interval_sec: float = 5.0) -> AsyncIterator[str]:
    """Yield SSE-formatted lines."""
    yield f"data: {json.dumps({'type': 'connected', 'timestamp': _utcnow()})}\n\n"
    while True:
        try:
            snap = await _snapshot_event()
            yield f"data: {json.dumps(snap, default=str)}\n\n"
        except asyncio.CancelledError:
            break
        except Exception as exc:
            err = {"type": "error", "message": str(exc), "timestamp": _utcnow()}
            yield f"data: {json.dumps(err)}\n\n"
        await asyncio.sleep(interval_sec)
