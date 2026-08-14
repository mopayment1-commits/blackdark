"""Paper options OMS — Deribit public chain + INTENT→FILL at mark (not live money)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_LOCK = threading.Lock()
_PATH = Path("data/options_oms.jsonl")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append(row: dict[str, Any]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOCK, _PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def list_orders(*, limit: int = 50) -> list[dict[str, Any]]:
    if not _PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    with _PATH.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows[-max(1, int(limit)) :]


async def chain_snapshot(currency: str = "BTC") -> dict[str, Any]:
    from options_fetcher import fetch_deribit_options_summary

    summary = await fetch_deribit_options_summary(currency)
    return {
        "ok": bool(summary.get("success")),
        "currency": currency.upper(),
        "provider": "deribit_public",
        "live_execution": False,
        "instruments": (summary.get("instruments") or [])[:25],
        "count": summary.get("count") or 0,
        "error": summary.get("error"),
    }


async def paper_fill(
    *,
    instrument: str,
    side: str,
    quantity: float,
    actor: str = "options_oms",
) -> dict[str, Any]:
    """Paper fill at Deribit mark. Never submits a live options order."""
    currency = "BTC"
    if instrument.upper().startswith("ETH"):
        currency = "ETH"
    snap = await chain_snapshot(currency)
    mark = None
    bid = None
    ask = None
    for inst in snap.get("instruments") or []:
        if str(inst.get("instrument") or "") == instrument:
            mark = inst.get("mark_price")
            bid = inst.get("bid")
            ask = inst.get("ask")
            break
    if mark is None and (snap.get("instruments") or []):
        first = snap["instruments"][0]
        instrument = str(first.get("instrument") or instrument)
        mark = first.get("mark_price")
        bid = first.get("bid")
        ask = first.get("ask")
    side_n = "buy" if str(side).lower() in {"buy", "long", "call"} else "sell"
    qty = max(0.01, float(quantity))
    order = {
        "order_id": f"opt_{uuid4().hex[:12]}",
        "instrument": instrument,
        "side": side_n,
        "quantity": qty,
        "state": "FILL",
        "fill_type": "paper_mark",
        "mark_price": mark,
        "bid": bid,
        "ask": ask,
        "live_execution": False,
        "history": ["INTENT", "RISK_CHECK", "ACK", "FILL"],
        "actor": actor,
        "created_at": _utcnow(),
    }
    _append(order)
    return {
        "ok": True,
        "live_execution": False,
        "order": order,
        "chain_ok": snap.get("ok"),
        "note": "Paper OMS at public mark — not a Deribit live order.",
    }
