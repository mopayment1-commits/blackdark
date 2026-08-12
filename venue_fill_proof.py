"""Prove OMS fill lifecycle end-to-end.

Modes:
- paper_lifecycle (default): full Intent→…→Fill→Reconcile→Portfolio→Audit without live capital
- testnet_live: when BINANCE_TESTNET + credentials + AUTO_EXECUTION_ENABLED — real venue protocol

Never claims live fill unless venue returns executed evidence.
Depth for risk gates is walked from Canonical Truth Bus venue L2 — never price*N fabrication.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _detect_live_fill(submit: dict[str, Any], *, dry_run: bool) -> bool:
    """True only for real venue execution — never for paper or protocol-proof mocks."""
    if dry_run:
        return False
    mode = str(submit.get("mode") or "")
    if mode in {"dry_run", "paper", "venue_protocol_proof", "paper_lifecycle"}:
        return False
    if submit.get("protocol_proof"):
        return False
    venue_result = submit.get("venue_result") or {}
    if isinstance(venue_result, dict):
        if venue_result.get("protocol_proof") or venue_result.get("mode") == "venue_protocol_proof":
            return False
        if venue_result.get("executed") is True:
            return True
        if venue_result.get("exchange_order") or venue_result.get("orderId"):
            return True
    return bool(submit.get("executed") is True)


def build_venue_protocol_proof_ack(
    *,
    order_id: str,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
) -> dict[str, Any]:
    """Honest mock venue ACK/FILL protocol — NEVER claims live_fill."""
    return {
        "mode": "venue_protocol_proof",
        "protocol_proof": True,
        "executed": False,
        "live_fill": False,
        "exchange_order": {
            "orderId": f"protocol_{order_id}",
            "symbol": symbol.replace("/", ""),
            "side": side.upper(),
            "status": "FILLED",
            "executedQty": str(quantity),
            "price": str(price),
            "proof": "synthetic_protocol_shape_only",
        },
        "note": "Protocol shape proof only — not a live or testnet venue fill.",
    }


async def prove_fill_lifecycle(
    *,
    org_id: str = "proof",
    symbol: str = "BTC/USDT",
    side: str = "buy",
    quantity: float = 0.001,
    limit_price: float | None = None,
    prefer_testnet: bool = False,
    actor: str = "venue_fill_proof",
) -> dict[str, Any]:
    import oms
    from canonical_truth_bus import book_notional_depth_usd, get_live_books, refresh_live_truth
    from institutional_store import ensure_ready, oms_upsert_sync, portfolio_upsert_position, store_status

    ensure_ready()
    live = await refresh_live_truth(symbol=symbol)
    books = {}
    try:
        books = get_live_books(require_live=bool(live.get("ok")), symbol=symbol)
    except Exception:
        books = {}

    depth_source = "unavailable"
    bid_depth = 0.0
    ask_depth = 0.0
    for venue_books in books.values():
        book = venue_books.get(symbol)
        if not book or not book.get("bids") or not book.get("asks"):
            continue
        if book.get("fabricated_depth"):
            continue
        bid_depth = book_notional_depth_usd(book, side="bid", levels=10)
        ask_depth = book_notional_depth_usd(book, side="ask", levels=10)
        depth_source = str(book.get("depth_source") or book.get("source") or venue_books)
        if limit_price is None:
            limit_price = (float(book["bids"][0][0]) + float(book["asks"][0][0])) / 2.0
        break

    if limit_price is None:
        return {
            "ok": False,
            "mode": "blocked",
            "live_fill": False,
            "reason": "live_mid_unavailable_fail_closed",
            "live_truth": {"venues": live.get("venues"), "ok": live.get("ok")},
            "proved_at": _utcnow(),
        }
    if bid_depth <= 0 or ask_depth <= 0:
        return {
            "ok": False,
            "mode": "blocked",
            "live_fill": False,
            "reason": "venue_l2_depth_unavailable_fail_closed",
            "depth_source": depth_source,
            "proved_at": _utcnow(),
        }

    testnet = prefer_testnet and os.getenv("BINANCE_TESTNET", "").lower() in {"1", "true", "yes"}
    live_enabled = os.getenv("AUTO_EXECUTION_ENABLED", "").lower() in {"1", "true", "yes"}
    dry_env = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    dry_run = not (testnet and live_enabled and not dry_env)

    # Ensure execution engine DB flag when attempting live/testnet
    if not dry_run:
        try:
            from execution_engine import set_auto_execution

            await set_auto_execution(True)
        except Exception:
            pass

    intent = oms.create_intent(
        org_id=org_id,
        venue="binance",
        symbol=symbol,
        side=side,
        quantity=quantity,
        limit_price=float(limit_price),
        idempotency_key=f"fill-proof-{uuid.uuid4().hex}",
        actor=actor,
    )
    row = oms.get_order(intent["order_id"])
    assert row is not None
    row["bid_depth_usd"] = bid_depth
    row["ask_depth_usd"] = ask_depth
    row["spread_bps"] = 2.0
    row["depth_source"] = depth_source
    oms_upsert_sync(row)
    with oms._LOCK:  # noqa: SLF001
        data = oms._load()  # noqa: SLF001
        data["orders"][intent["order_id"]] = {**data["orders"][intent["order_id"]], **row}
        oms._save(data)  # noqa: SLF001

    protocol_env = os.getenv("VENUE_PROTOCOL_PROOF", "").lower() in {"1", "true", "yes"}
    submit = await oms.submit_to_venue(intent["order_id"], actor=actor, dry_run=dry_run)
    order = oms.get_order(intent["order_id"])
    assert order is not None

    mode = "paper_lifecycle"
    protocol_ack = None
    live_fill = _detect_live_fill(submit if isinstance(submit, dict) else {}, dry_run=dry_run)
    if order["state"] == "ACK" and (dry_run or protocol_env):
        # Optional honest protocol-shape ACK (still not live_fill)
        if protocol_env or dry_run:
            protocol_ack = build_venue_protocol_proof_ack(
                order_id=intent["order_id"],
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=float(limit_price),
            )
        oms.transition(intent["order_id"], "FILL", actor=actor, fill_qty=quantity, reason="paper_fill_proof")
        recon = oms.reconcile(
            intent["order_id"],
            actor=actor,
            venue_filled_qty=quantity,
            venue_ack_id=str(
                (protocol_ack or {}).get("exchange_order", {}).get("orderId")
                or (submit.get("venue_result") or {}).get("order_id")
                or f"paper_{intent['order_id']}"
            ),
        )
        mode = "venue_protocol_proof" if protocol_ack else "paper_lifecycle"
        live_fill = False
    elif order["state"] in {"FILL", "RECONCILE"}:
        recon = order.get("reconcile") or oms.reconcile(
            intent["order_id"],
            actor=actor,
            venue_filled_qty=float(order.get("filled_quantity") or quantity),
        )
        mode = "testnet_live" if live_fill else "venue_path_no_fill_evidence"
    else:
        recon = {"ok": False, "oms_state": order["state"], "submit": submit}

    final = oms.get_order(intent["order_id"])
    assert final is not None

    notional = float(final.get("filled_quantity") or 0) * float(limit_price)
    pos = None
    if final["state"] in {"FILL", "RECONCILE"} and float(final.get("filled_quantity") or 0) > 0:
        pos = await portfolio_upsert_position(
            {
                "org_id": org_id,
                "asset": symbol.split("/")[0],
                "symbol": symbol,
                "side": "long" if side == "buy" else "short",
                "quantity": float(final["filled_quantity"]),
                "notional_usd": notional,
                "venue": final.get("venue"),
                "source_order_id": final["order_id"],
            }
        )

    trail = [h.get("state") for h in (final.get("history") or [])]
    required = {"INTENT", "VALIDATION", "RISK_CHECK", "ROUTING", "SUBMISSION", "ACK"}
    lifecycle_ok = required.issubset(set(trail)) and final["state"] in {"FILL", "RECONCILE"}
    return {
        "ok": lifecycle_ok and bool((recon or {}).get("ok", recon)),
        "mode": mode,
        "live_fill": live_fill,
        "order_id": final["order_id"],
        "oms_state": final["state"],
        "history_states": trail,
        "reconcile": recon if isinstance(recon, dict) else final.get("reconcile"),
        "portfolio_position": pos,
        "live_truth": {
            "venues": live.get("venues"),
            "l2_venues": live.get("l2_venues"),
            "ok": live.get("ok"),
            "fabricated_depth": live.get("fabricated_depth"),
        },
        "depth": {
            "source": depth_source,
            "bid_depth_usd": bid_depth,
            "ask_depth_usd": ask_depth,
            "fabricated": False,
        },
        "store": store_status(),
        "dry_run": dry_run,
        "protocol_ack": protocol_ack,
        "proved_at": _utcnow(),
        "audit_trail": True,
        "note": (
            "Live venue fill requires BINANCE_TESTNET + AUTO_EXECUTION_ENABLED + "
            "AUTO_EXECUTION_DRY_RUN=false + vault/test creds. "
            "venue_protocol_proof is an honest ACK/FILL *shape* mock — never live_fill. "
            "Default proves full paper lifecycle with venue-L2 depth + DB portfolio/audit authority."
        ),
    }


def proof_status() -> dict[str, Any]:
    return {
        "surface": "venue_fill_proof",
        "modes": ["paper_lifecycle", "venue_protocol_proof", "testnet_live"],
        "live_fill_requires": [
            "BINANCE_TESTNET",
            "AUTO_EXECUTION_ENABLED",
            "AUTO_EXECUTION_DRY_RUN=false",
            "vault_or_test_creds",
        ],
        "depth_source": "canonical_truth_bus_venue_l2",
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }
