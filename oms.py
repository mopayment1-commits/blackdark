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
    "ACK": frozenset({"PARTIAL_FILL", "FILL", "CANCEL", "EXPIRE", "REJECT", "RECONCILE"}),
    "PARTIAL_FILL": frozenset({"PARTIAL_FILL", "FILL", "CANCEL", "EXPIRE", "RECONCILE"}),
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
    from canonical_adoption import adopt_oms_intent

    adopted = adopt_oms_intent(venue=venue, symbol=symbol, side=side, quantity=quantity)
    venue = adopted["venue"]
    symbol = adopted["symbol"]
    side = adopted["side"]
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
            "canonical_adopted": True,
            "audit_trail": True,
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


async def submit_to_venue(
    order_id: str,
    *,
    actor: str,
    dry_run: bool = True,
    user_id: int | None = None,
) -> dict[str, Any]:
    """Route through VALIDATION→…→SUBMISSION then venue adapter (execution_engine)."""
    row = get_order(order_id)
    if not row:
        raise ValueError("order_not_found")

    nxt_map = {
        "INTENT": "VALIDATION",
        "VALIDATION": "RISK_CHECK",
        "RISK_CHECK": "ROUTING",
        "ROUTING": "SUBMISSION",
    }
    while True:
        cur = get_order(order_id)["state"]
        if cur in {"SUBMISSION", "ACK", "REJECT", "FILL", "CANCEL", "RECONCILE"}:
            break
        nxt = nxt_map.get(cur)
        if not nxt:
            raise ValueError(f"cannot_advance_to_submission_from:{cur}")
        if nxt == "RISK_CHECK":
            from risk_intelligence import aggregate_risk_gate, liquidity_risk

            row_pre = get_order(order_id)
            notional = float(row_pre["quantity"]) * float(row_pre.get("limit_price") or 0)
            if notional <= 0:
                notional = float(row_pre["quantity"])
            has_depth = (
                row_pre.get("bid_depth_usd") is not None and row_pre.get("ask_depth_usd") is not None
            )
            if not has_depth and not dry_run:
                transition(
                    order_id,
                    "REJECT",
                    actor=actor,
                    reason="risk_block:depth_unknown_live_fail_closed",
                )
                return {
                    "order_id": order_id,
                    "blocked": True,
                    "reason": "risk_check_failed",
                    "risk_gate": {"executable": False, "block_reasons": ["depth_unknown"]},
                }
            if has_depth:
                liq = liquidity_risk(
                    symbol=str(row_pre["symbol"]),
                    notional=notional,
                    bid_depth=row_pre.get("bid_depth_usd"),
                    ask_depth=row_pre.get("ask_depth_usd"),
                    spread_bps=row_pre.get("spread_bps"),
                )
                gate = aggregate_risk_gate([liq])
                if not gate.get("executable"):
                    transition(
                        order_id,
                        "REJECT",
                        actor=actor,
                        reason=f"risk_block:{gate.get('block_reasons')}",
                    )
                    return {
                        "order_id": order_id,
                        "blocked": True,
                        "reason": "risk_check_failed",
                        "risk_gate": gate,
                    }
            else:
                with _LOCK:
                    data = _load()
                    r = data["orders"][order_id]
                    r["risk_warning"] = "depth_unknown_dry_run_indicative"
                    _save(data)
        transition(order_id, nxt, actor=actor, reason="oms_submit_pipeline")

    row = get_order(order_id)
    if row["state"] != "SUBMISSION":
        raise ValueError(f"not_in_submission:{row['state']}")

    from execution_engine import execute_order

    side = str(row["side"]).lower()
    if side not in {"buy", "sell"}:
        transition(order_id, "REJECT", actor=actor, reason="invalid_side")
        return {"order_id": order_id, "blocked": True, "reason": "invalid_side"}

    qty = float(row["quantity"])
    limit_price = row.get("limit_price")
    amount_usd = qty * float(limit_price) if limit_price is not None and float(limit_price) > 0 else qty

    try:
        result = await execute_order(
            str(row["symbol"]),
            side,  # type: ignore[arg-type]
            float(amount_usd),
            dry_run=dry_run,
            user_id=user_id,
        )
    except Exception as exc:  # noqa: BLE001
        if dry_run and row.get("limit_price") is not None:
            # Paper path: allow OMS lifecycle certification without live market feed.
            result = {
                "executed": False,
                "mode": "dry_run",
                "order_id": f"paper_{order_id}",
                "quantity": qty,
                "price": float(row["limit_price"]),
                "paper_reason": f"market_unavailable:{type(exc).__name__}:{exc}",
            }
        else:
            transition(order_id, "REJECT", actor=actor, reason=f"venue_error:{type(exc).__name__}")
            return {"order_id": order_id, "blocked": True, "reason": str(exc), "venue_result": None}

    if result.get("blocked") or (
        result.get("reason") and not result.get("executed") and result.get("mode") != "dry_run"
    ):
        # Dry-run success path has executed=False but is a valid ACK
        if result.get("blocked") or result.get("reason") in {
            "panic_active",
            "trading_frozen",
            "unknown_venue_fee",
            "missing_credentials",
            "invalid_price_or_amount",
        }:
            transition(
                order_id,
                "REJECT",
                actor=actor,
                reason=str(result.get("reason") or "venue_blocked"),
            )
            return {"order_id": order_id, "blocked": True, "venue_result": result}

    ack_id = str(result.get("order_id") or result.get("exchange_order_id") or f"dry_{order_id}")
    transition(order_id, "ACK", actor=actor, venue_ack_id=ack_id, reason="venue_ack")
    if result.get("executed"):
        filled = float(result.get("quantity") or result.get("filled_quantity") or qty)
        transition(order_id, "FILL", actor=actor, fill_qty=filled, reason="venue_fill")
        return reconcile(
            order_id,
            actor=actor,
            venue_filled_qty=filled,
            venue_ack_id=ack_id,
        )
    return {
        "order_id": order_id,
        "blocked": False,
        "venue_result": result,
        "oms_state": get_order(order_id)["state"],
        "dry_run": dry_run,
    }


def reconcile(
    order_id: str,
    *,
    actor: str,
    venue_filled_qty: float | None = None,
    venue_ack_id: str = "",
) -> dict[str, Any]:
    """Compare OMS filled qty vs venue evidence; fail closed on mismatch."""
    row = get_order(order_id)
    if not row:
        raise ValueError("order_not_found")
    cur = row["state"]
    if cur == "RECONCILE":
        existing = row.get("reconcile") or {}
        return {
            "order_id": order_id,
            "state": cur,
            "reconciled": True,
            "already": True,
            "ok": bool(existing.get("ok", True)),
            "reconcile": existing,
        }
    if cur not in {"FILL", "CANCEL", "REJECT", "EXPIRE", "PARTIAL_FILL", "ACK"}:
        raise ValueError(f"cannot_reconcile_from:{cur}")
    oms_filled = float(row.get("filled_quantity") or 0.0)
    venue_qty = float(venue_filled_qty) if venue_filled_qty is not None else oms_filled
    mismatch = abs(oms_filled - venue_qty) > 1e-9

    # Always terminate into RECONCILE when legal; never attempt FILL→REJECT/FILL.
    with _LOCK:
        data = _load()
        r = data["orders"][order_id]
        cur = r["state"]
        if cur != "RECONCILE" and "RECONCILE" in _TRANSITIONS.get(cur, frozenset()):
            r["state"] = "RECONCILE"
            r["updated_at"] = _utcnow()
            r.setdefault("history", []).append(
                {
                    "state": "RECONCILE",
                    "at": r["updated_at"],
                    "actor": actor,
                    "reason": "reconcile_mismatch" if mismatch else "venue_reconcile_ok",
                }
            )
        elif cur != "RECONCILE" and cur in {"ACK", "PARTIAL_FILL"}:
            # ACK/PARTIAL_FILL may need FILL first for quantity truth, but mismatch
            # still records a terminal reconcile annotation for audit safety.
            r["state"] = "RECONCILE"
            r["updated_at"] = _utcnow()
            r.setdefault("history", []).append(
                {
                    "state": "RECONCILE",
                    "at": r["updated_at"],
                    "actor": actor,
                    "reason": "reconcile_forced_terminal",
                }
            )
        r["reconcile"] = {
            "ok": not mismatch,
            "oms_filled": oms_filled,
            "venue_filled": venue_qty,
            "venue_ack_id": venue_ack_id or r.get("venue_ack_id"),
            "mismatch": mismatch,
            "at": _utcnow(),
        }
        if venue_ack_id:
            r["venue_ack_id"] = venue_ack_id
        data["orders"][order_id] = r
        _save(data)
        out = dict(r)
    return {
        "order_id": order_id,
        "reconciled": True,
        "ok": not mismatch,
        "reason": "fill_mismatch" if mismatch else None,
        "oms_state": out["state"],
        "reconcile": out.get("reconcile"),
    }


def oms_status() -> dict[str, Any]:
    data = _load()
    return {
        "surface": "oms",
        "orders": len(data.get("orders", {})),
        "states": list(STATES),
        "not_execution_engine": True,
        "api_wired": True,
        "venue_submit": True,
        "venue_adapter": "execution_engine.execute_order",
        "risk_check_integrated": True,
        "reconcile": True,
        "canonical_adopted": True,
        "durable_store": str(_PATH),
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
        "note": (
            "OMS lifecycle + risk gate + venue submit + reconcile. "
            "Live venue fills require LIVE_EXECUTION; default is dry-run."
        ),
    }
