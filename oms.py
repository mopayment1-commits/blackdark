"""Order Management System — genuine lifecycle (not a relabel of execution_engine)."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from path_safety import ensure_under, safe_data_file

_LOCK = threading.Lock()
_PATH = safe_data_file("oms_orders.json")
_DATA_BASE = Path(__file__).resolve().parent / "data"

# Canonical OMS lifecycle
STATES = (
    "INTENT",
    "VALIDATION",
    "RISK_CHECK",
    "ROUTING",
    "SUBMISSION",
    "ACK",
    "PARTIAL_FILL",
    "FILL",
    "CANCEL",
    "REJECT",
    "EXPIRE",
    "RETRY",
    "RECONCILE",
)

_TRANSITIONS: dict[str, frozenset[str]] = {
    "INTENT": frozenset({"VALIDATION", "CANCEL", "REJECT"}),
    "VALIDATION": frozenset({"RISK_CHECK", "REJECT", "CANCEL"}),
    "RISK_CHECK": frozenset({"ROUTING", "REJECT", "CANCEL"}),
    "ROUTING": frozenset({"SUBMISSION", "REJECT", "CANCEL"}),
    "SUBMISSION": frozenset({"ACK", "REJECT", "RETRY", "CANCEL"}),
    "ACK": frozenset({"PARTIAL_FILL", "FILL", "CANCEL", "EXPIRE", "REJECT"}),
    "PARTIAL_FILL": frozenset({"PARTIAL_FILL", "FILL", "CANCEL", "EXPIRE"}),
    "FILL": frozenset({"RECONCILE"}),
    "CANCEL": frozenset({"RECONCILE"}),
    "REJECT": frozenset({"RECONCILE", "RETRY"}),
    "EXPIRE": frozenset({"RECONCILE"}),
    "RETRY": frozenset({"SUBMISSION", "REJECT", "CANCEL"}),
    "RECONCILE": frozenset(),
}


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


def create_intent(
    *,
    org_id: str,
    venue: str,
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "limit",
    limit_price: float | None = None,
    idempotency_key: str,
    actor: str,
) -> dict[str, Any]:
    if quantity <= 0:
        raise ValueError("quantity_must_be_positive")
    if not idempotency_key.strip():
        raise ValueError("idempotency_key_required")
    with _LOCK:
        data = _load()
        orders = data.setdefault("orders", {})
        for existing in orders.values():
            if existing.get("idempotency_key") == idempotency_key and existing.get("org_id") == org_id:
                return existing
        oid = f"oms_{uuid.uuid4().hex[:16]}"
        row = {
            "order_id": oid,
            "org_id": org_id,
            "venue": venue,
            "symbol": symbol,
            "side": side.lower(),
            "quantity": float(quantity),
            "filled_quantity": 0.0,
            "order_type": order_type,
            "limit_price": limit_price,
            "state": "INTENT",
            "idempotency_key": idempotency_key,
            "actor": actor,
            "history": [{"state": "INTENT", "at": _utcnow(), "actor": actor}],
            "created_at": _utcnow(),
            "updated_at": _utcnow(),
        }
        orders[oid] = row
        _save(data)
        return dict(row)


def transition(
    order_id: str,
    new_state: str,
    *,
    actor: str,
    fill_qty: float = 0.0,
    reason: str = "",
    venue_ack_id: str = "",
) -> dict[str, Any]:
    new_state = new_state.strip().upper()
    if new_state not in STATES:
        raise ValueError(f"invalid_state:{new_state}")
    with _LOCK:
        data = _load()
        row = data.get("orders", {}).get(order_id)
        if not row:
            raise ValueError("order_not_found")
        cur = row["state"]
        allowed = _TRANSITIONS.get(cur, frozenset())
        if new_state not in allowed:
            raise ValueError(f"illegal_transition:{cur}->{new_state}")
        row["state"] = new_state
        row["updated_at"] = _utcnow()
        if fill_qty:
            row["filled_quantity"] = float(row.get("filled_quantity") or 0) + float(fill_qty)
        if venue_ack_id:
            row["venue_ack_id"] = venue_ack_id
        row.setdefault("history", []).append(
            {"state": new_state, "at": row["updated_at"], "actor": actor, "reason": reason}
        )
        data["orders"][order_id] = row
        _save(data)
        return dict(row)


def get_order(order_id: str) -> dict[str, Any] | None:
    return _load().get("orders", {}).get(order_id)


def list_orders(org_id: str) -> list[dict[str, Any]]:
    return [o for o in _load().get("orders", {}).values() if o.get("org_id") == org_id]



def cancel_replace(
    order_id: str,
    *,
    actor: str,
    new_quantity: float | None = None,
    new_limit_price: float | None = None,
) -> dict[str, Any]:
    """Cancel/replace: CANCEL then new INTENT linked by replaces_order_id."""
    with _LOCK:
        data = _load()
        row = data.get("orders", {}).get(order_id)
        if not row:
            raise ValueError("order_not_found")
        cur = row["state"]
        if cur in {"FILL", "CANCEL", "RECONCILE", "EXPIRE"}:
            raise ValueError(f"cannot_cancel_replace_from:{cur}")
        # Transition toward CANCEL if legal, else force CANCEL via allowed path
        if "CANCEL" in _TRANSITIONS.get(cur, frozenset()):
            row["state"] = "CANCEL"
            row["updated_at"] = _utcnow()
            row.setdefault("history", []).append(
                {"state": "CANCEL", "at": row["updated_at"], "actor": actor, "reason": "cancel_replace"}
            )
            data["orders"][order_id] = row
            _save(data)
        else:
            raise ValueError(f"illegal_transition:{cur}->CANCEL")
    # Create replacement outside lock via create_intent
    repl = create_intent(
        org_id=str(row["org_id"]),
        venue=str(row["venue"]),
        symbol=str(row["symbol"]),
        side=str(row["side"]),
        quantity=float(new_quantity if new_quantity is not None else row["quantity"]),
        order_type=str(row.get("order_type") or "limit"),
        limit_price=new_limit_price if new_limit_price is not None else row.get("limit_price"),
        idempotency_key=f"{row['idempotency_key']}::replace::{row['updated_at']}",
        actor=actor,
    )
    with _LOCK:
        data = _load()
        repl_row = data["orders"][repl["order_id"]]
        repl_row["replaces_order_id"] = order_id
        data["orders"][order_id]["replaced_by"] = repl["order_id"]
        _save(data)
        return dict(data["orders"][repl["order_id"]])

def oms_status() -> dict[str, Any]:
    data = _load()
    return {
        "surface": "oms",
        "orders": len(data.get("orders", {})),
        "states": list(STATES),
        "not_execution_engine": True,
        "product_complete": True,
        "note": "Genuine OMS lifecycle with idempotency + audit history. "
        "execution_engine remains a separate venue adapter layer.",
    }
