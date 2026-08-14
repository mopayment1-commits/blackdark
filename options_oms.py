"""Paper options OMS — genuine lifecycle at Deribit public mark (never live money)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("options_oms.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"

STATES = (
    "INTENT",
    "VALIDATION",
    "RISK_CHECK",
    "ACK",
    "FILL",
    "REJECT",
    "RECONCILE",
)
_TRANSITIONS: dict[str, frozenset[str]] = {
    "INTENT": frozenset({"VALIDATION", "REJECT"}),
    "VALIDATION": frozenset({"RISK_CHECK", "REJECT"}),
    "RISK_CHECK": frozenset({"ACK", "REJECT"}),
    "ACK": frozenset({"FILL", "REJECT"}),
    "FILL": frozenset({"RECONCILE"}),
    "REJECT": frozenset({"RECONCILE"}),
    "RECONCILE": frozenset(),
}
MAX_QTY = 100.0
MIN_QTY = 0.01


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load() -> dict[str, Any]:
    if not _PATH.exists():
        return {"orders": {}}
    try:
        return json.loads(_PATH.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return {"orders": {}}


def _save(data: dict[str, Any]) -> None:
    path = ensure_under(_PATH, _DATA_BASE)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _transition(row: dict[str, Any], new_state: str, *, note: str = "") -> dict[str, Any]:
    current = str(row.get("state") or "INTENT")
    allowed = _TRANSITIONS.get(current, frozenset())
    if new_state not in allowed:
        raise ValueError(f"illegal_transition:{current}->{new_state}")
    hist = list(row.get("history") or [])
    hist.append({"state": new_state, "at": _utcnow(), "note": note})
    row["state"] = new_state
    row["history"] = hist
    row["updated_at"] = _utcnow()
    return row


def list_orders(*, limit: int = 50) -> list[dict[str, Any]]:
    orders = list((_load().get("orders") or {}).values())
    orders.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return orders[: max(1, int(limit))]


def get_order(order_id: str) -> dict[str, Any] | None:
    return (_load().get("orders") or {}).get(order_id)


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


def _find_instrument(snapshot: dict[str, Any], instrument: str) -> dict[str, Any] | None:
    wanted = str(instrument or "").strip()
    for inst in snapshot.get("instruments") or []:
        if str(inst.get("instrument") or "") == wanted:
            return inst
    return None


def _persist(row: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        data = _load()
        data.setdefault("orders", {})[row["order_id"]] = row
        _save(data)
    return dict(row)


async def paper_cycle(
    *,
    instrument: str,
    side: str,
    quantity: float,
    actor: str = "options_oms",
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """INTENT→VALIDATION→RISK_CHECK→ACK→FILL→RECONCILE at public mark. Never live."""
    side_n = str(side or "").lower().strip()
    if side_n in {"long", "call"}:
        side_n = "buy"
    if side_n in {"short", "put"}:
        side_n = "sell"
    qty = float(quantity)
    currency = "ETH" if str(instrument).upper().startswith("ETH") else "BTC"
    snap = snapshot if snapshot is not None else await chain_snapshot(currency)
    row: dict[str, Any] = {
        "order_id": f"opt_{uuid4().hex[:12]}",
        "instrument": str(instrument or "").strip(),
        "side": side_n,
        "quantity": qty,
        "state": "INTENT",
        "live_execution": False,
        "fill_type": "paper_mark",
        "actor": actor,
        "history": [{"state": "INTENT", "at": _utcnow(), "note": "created"}],
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }
    _persist(row)

    if side_n not in {"buy", "sell"} or qty < MIN_QTY or qty > MAX_QTY or not row["instrument"]:
        _transition(row, "VALIDATION", note="invalid_side_or_qty")
        _transition(row, "REJECT", note="validation_failed")
        _transition(row, "RECONCILE", note="rejected")
        row["ok"] = False
        row["reason"] = "validation_failed"
        return {"ok": False, "live_execution": False, "order": _persist(row), "reason": row["reason"]}

    _transition(row, "VALIDATION", note="ok")
    inst = _find_instrument(snap, row["instrument"])
    if not inst:
        _transition(row, "RISK_CHECK", note="instrument_missing")
        _transition(row, "REJECT", note="unknown_instrument_no_silent_swap")
        _transition(row, "RECONCILE", note="rejected")
        row["ok"] = False
        row["reason"] = "unknown_instrument"
        row["chain_ok"] = bool(snap.get("ok"))
        return {"ok": False, "live_execution": False, "order": _persist(row), "reason": row["reason"]}

    mark = inst.get("mark_price")
    bid = inst.get("bid")
    ask = inst.get("ask")
    row["mark_price"] = mark
    row["bid"] = bid
    row["ask"] = ask
    if mark is None or float(mark) <= 0:
        _transition(row, "RISK_CHECK", note="mark_unavailable")
        _transition(row, "REJECT", note="no_mark")
        _transition(row, "RECONCILE", note="rejected")
        row["ok"] = False
        row["reason"] = "mark_unavailable"
        return {"ok": False, "live_execution": False, "order": _persist(row), "reason": row["reason"]}

    _transition(row, "RISK_CHECK", note="mark_ok")
    _transition(row, "ACK", note="paper_ack")
    _transition(row, "FILL", note="paper_fill_at_mark")
    _transition(row, "RECONCILE", note="paper_reconcile")
    row["ok"] = True
    row["reason"] = None
    row["chain_ok"] = bool(snap.get("ok"))
    persisted = _persist(row)
    return {
        "ok": True,
        "live_execution": False,
        "order": persisted,
        "chain_ok": bool(snap.get("ok")),
        "note": "Paper OMS at public mark — not a Deribit live order.",
    }


async def paper_fill(
    *,
    instrument: str,
    side: str,
    quantity: float,
    actor: str = "options_oms",
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Back-compat alias for paper_cycle."""
    return await paper_cycle(
        instrument=instrument,
        side=side,
        quantity=quantity,
        actor=actor,
        snapshot=snapshot,
    )
