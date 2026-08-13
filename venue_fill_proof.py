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


def _arm_testnet_live_env(*, restore: dict[str, str | None] | None = None) -> dict[str, str | None]:
    """Temporarily arm testnet live flags for an explicit prove (non-production).

    Does not invent credentials. Caller must restore via returned previous values.
    """
    keys = ("BINANCE_TESTNET", "AUTO_EXECUTION_ENABLED", "AUTO_EXECUTION_DRY_RUN")
    if restore is not None:
        for k, prev in restore.items():
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev
        return {}
    previous = {k: os.getenv(k) for k in keys}
    os.environ["BINANCE_TESTNET"] = "true"
    os.environ["AUTO_EXECUTION_ENABLED"] = "true"
    os.environ["AUTO_EXECUTION_DRY_RUN"] = "false"
    return previous


async def prove_fill_lifecycle(
    *,
    org_id: str = "proof",
    symbol: str = "BTC/USDT",
    side: str = "buy",
    quantity: float = 0.001,
    limit_price: float | None = None,
    prefer_testnet: bool = False,
    arm_testnet_live: bool = False,
    actor: str = "venue_fill_proof",
) -> dict[str, Any]:
    import oms
    from canonical_truth_bus import book_notional_depth_usd, get_live_books, refresh_live_truth
    from institutional_store import ensure_ready, oms_upsert_sync, portfolio_upsert_position, store_status

    ensure_ready()
    has_binance_creds = bool(
        os.getenv("BINANCE_API_KEY", "").strip() and os.getenv("BINANCE_API_SECRET", "").strip()
    )
    # Explicit prove arming: only when operator requested AND HMAC creds are present.
    env_restore: dict[str, str | None] | None = None
    if arm_testnet_live and has_binance_creds:
        env_restore = _arm_testnet_live_env()

    live = await refresh_live_truth(symbol=symbol)
    books = {}
    try:
        books = get_live_books(require_live=bool(live.get("ok")), symbol=symbol)
    except Exception:
        books = {}

    depth_source = "unavailable"
    bid_depth = 0.0
    ask_depth = 0.0
    depth_venue = None
    depth_book: dict[str, Any] | None = None
    secondary_l2_venues: list[str] = []
    for venue_name, venue_books in books.items():
        book = venue_books.get(symbol)
        if not book or not book.get("bids") or not book.get("asks"):
            continue
        if book.get("fabricated_depth"):
            continue
        vname = str(venue_name).lower()
        if depth_venue is None:
            bid_depth = book_notional_depth_usd(book, side="bid", levels=10)
            ask_depth = book_notional_depth_usd(book, side="ask", levels=10)
            depth_source = str(book.get("depth_source") or book.get("source") or "venue_l2")
            depth_venue = vname
            depth_book = book
            if limit_price is None:
                limit_price = (float(book["bids"][0][0]) + float(book["asks"][0][0])) / 2.0
        else:
            secondary_l2_venues.append(vname)

    if limit_price is None:
        if env_restore is not None:
            _arm_testnet_live_env(restore=env_restore)
        return {
            "ok": False,
            "mode": "blocked",
            "live_fill": False,
            "reason": "live_mid_unavailable_fail_closed",
            "live_truth": {"venues": live.get("venues"), "ok": live.get("ok")},
            "proved_at": _utcnow(),
        }
    if bid_depth <= 0 or ask_depth <= 0:
        if env_restore is not None:
            _arm_testnet_live_env(restore=env_restore)
        return {
            "ok": False,
            "mode": "blocked",
            "live_fill": False,
            "reason": "venue_l2_depth_unavailable_fail_closed",
            "depth_source": depth_source,
            "proved_at": _utcnow(),
        }

    testnet = os.getenv("BINANCE_TESTNET", "").lower() in {"1", "true", "yes"} or prefer_testnet
    live_enabled = os.getenv("AUTO_EXECUTION_ENABLED", "").lower() in {"1", "true", "yes"}
    dry_env = os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}
    # Live/testnet fill only when testnet+flags+creds — never invent live_fill.
    dry_run = not (testnet and live_enabled and not dry_env and has_binance_creds)

    order_host_probe: dict[str, Any] = {}
    external_block: str | None = None
    if not dry_run:
        try:
            from execution_engine import probe_binance_order_host_connectivity

            order_host_probe = await probe_binance_order_host_connectivity()
            if order_host_probe.get("geo_blocked") and not order_host_probe.get("ok"):
                external_block = str(order_host_probe.get("external_block") or "binance_order_host_geo_451")
        except Exception as exc:  # noqa: BLE001
            order_host_probe = {"ok": False, "reason": type(exc).__name__}

    # Paper/protocol venue identity follows the L2 book venue (not hard-coded binance).
    # Live Binance testnet execution still routes via execution_engine when dry_run=False.
    paper_venue = depth_venue or (live.get("l2_venues") or ["okx"])[0]
    exec_venue = "binance" if not dry_run else str(paper_venue)

    # Ensure execution engine DB flag when attempting live/testnet
    if not dry_run and not external_block:
        try:
            from execution_engine import set_auto_execution

            await set_auto_execution(True)
        except Exception:
            pass

    intent = oms.create_intent(
        org_id=org_id,
        venue=exec_venue,
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
    # Real L2 mid spread when book available (never hardcode theater bps).
    live_spread_bps = None
    if depth_book and depth_book.get("bids") and depth_book.get("asks"):
        bb = float(depth_book["bids"][0][0])
        ba = float(depth_book["asks"][0][0])
        mid = (bb + ba) / 2.0
        if mid > 0:
            live_spread_bps = ((ba - bb) / mid) * 10_000
    row["spread_bps"] = float(live_spread_bps if live_spread_bps is not None else 2.0)
    row["depth_source"] = depth_source
    oms_upsert_sync(row)
    with oms._LOCK:  # noqa: SLF001
        data = oms._load()  # noqa: SLF001
        data["orders"][intent["order_id"]] = {**data["orders"][intent["order_id"]], **row}
        oms._save(data)  # noqa: SLF001

    try:
        protocol_env = os.getenv("VENUE_PROTOCOL_PROOF", "").lower() in {"1", "true", "yes"}
        # Geo-blocked order hosts: do not pretend a live path; fall back to paper evidence only.
        effective_dry_run = dry_run or bool(external_block)
        submit = await oms.submit_to_venue(
            intent["order_id"], actor=actor, dry_run=effective_dry_run
        )
        order = oms.get_order(intent["order_id"])
        assert order is not None

        mode = "paper_lifecycle"
        protocol_ack = None
        live_fill = _detect_live_fill(
            submit if isinstance(submit, dict) else {}, dry_run=effective_dry_run
        )
        if external_block:
            live_fill = False
            mode = "external_block_geo"
        if order["state"] == "ACK" and (effective_dry_run or protocol_env):
            if protocol_env or effective_dry_run:
                protocol_ack = build_venue_protocol_proof_ack(
                    order_id=intent["order_id"],
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=float(limit_price),
                )
            oms.transition(
                intent["order_id"], "FILL", actor=actor, fill_qty=quantity, reason="paper_fill_proof"
            )
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
            if not external_block:
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

        book_walk: dict[str, Any] = {"ok": False, "reason": "no_depth_book"}
        if depth_book is not None:
            try:
                from microstructure_intelligence import order_book_microstructure

                walk_notional = float(quantity) * float(limit_price)
                micro = order_book_microstructure(depth_book, notional=max(walk_notional, 1.0))
                levels = depth_book.get("asks" if side == "buy" else "bids") or []
                remaining = float(quantity)
                consumed = 0
                vwap_num = 0.0
                vwap_den = 0.0
                for px, qty, *_ in levels:
                    take = min(remaining, float(qty))
                    if take <= 0:
                        break
                    vwap_num += float(px) * take
                    vwap_den += take
                    remaining -= take
                    consumed += 1
                    if remaining <= 1e-12:
                        break
                filled_qty = float(quantity) - remaining
                vwap = (vwap_num / vwap_den) if vwap_den > 0 else None
                mid = micro.get("mid") or float(limit_price)
                impact_bps = None
                if vwap is not None and mid > 0:
                    raw = ((vwap - mid) / mid) * 10_000
                    impact_bps = abs(raw) if side == "buy" else abs(-raw)
                alt_walks: list[dict[str, Any]] = []
                for alt_venue in secondary_l2_venues[:3]:
                    alt_book = (books.get(alt_venue) or {}).get(symbol)
                    if not alt_book or not alt_book.get("bids") or not alt_book.get("asks"):
                        continue
                    if alt_book.get("fabricated_depth"):
                        continue
                    alt_levels = alt_book.get("asks" if side == "buy" else "bids") or []
                    alt_rem = float(quantity)
                    alt_num = 0.0
                    alt_den = 0.0
                    alt_consumed = 0
                    for px, qty, *_ in alt_levels:
                        take = min(alt_rem, float(qty))
                        if take <= 0:
                            break
                        alt_num += float(px) * take
                        alt_den += take
                        alt_rem -= take
                        alt_consumed += 1
                        if alt_rem <= 1e-12:
                            break
                    alt_vwap = (alt_num / alt_den) if alt_den > 0 else None
                    alt_mid = (
                        (float(alt_book["bids"][0][0]) + float(alt_book["asks"][0][0])) / 2.0
                    )
                    alt_impact = None
                    if alt_vwap is not None and alt_mid > 0:
                        alt_impact = abs(((alt_vwap - alt_mid) / alt_mid) * 10_000)
                    alt_walks.append(
                        {
                            "venue": alt_venue,
                            "levels_consumed": alt_consumed,
                            "impact_bps": round(alt_impact, 4) if alt_impact is not None else None,
                            "live_fill": False,
                        }
                    )

                cancel_replace = {
                    "ok": False,
                    "live_fill": False,
                    "note": "paper_cancel_replace_shape",
                }
                try:
                    if final["state"] in {"FILL", "RECONCILE", "ACK"}:
                        cancel_replace = {
                            "ok": True,
                            "steps": ["ACK", "CANCEL_SHAPE", "REPLACE_SHAPE", "RE_ACK_SHAPE"],
                            "replaced_quantity": float(quantity),
                            "replaced_limit": float(limit_price),
                            "live_fill": False,
                            "note": "Shape-only cancel/replace evidence on paper path — not venue ACK.",
                        }
                except Exception as exc:  # noqa: BLE001
                    cancel_replace = {"ok": False, "reason": type(exc).__name__, "live_fill": False}

                book_walk = {
                    "ok": filled_qty > 0 and consumed >= 1,
                    "venue": depth_venue,
                    "side": side,
                    "quantity": float(quantity),
                    "levels_consumed": consumed,
                    "filled_qty_on_book": filled_qty,
                    "unfilled_qty": max(0.0, remaining),
                    "vwap": vwap,
                    "impact_bps": round(impact_bps, 4) if impact_bps is not None else None,
                    "capacity_usd": micro.get("capacity_usd"),
                    "spread_bps": micro.get("spread_bps"),
                    "live_spread_bps": live_spread_bps,
                    "participation": micro.get("participation"),
                    "alt_venue_walks": alt_walks,
                    "cancel_replace": cancel_replace,
                    "live_fill": False,
                    "note": "Paper book-walk against venue L2 — impact evidence only, not venue ACK.",
                }
            except Exception as exc:  # noqa: BLE001
                book_walk = {"ok": False, "reason": type(exc).__name__, "live_fill": False}

        blocking = []
        if dry_run:
            if not testnet:
                blocking.append("BINANCE_TESTNET")
            if not live_enabled:
                blocking.append("AUTO_EXECUTION_ENABLED")
            if dry_env:
                blocking.append("AUTO_EXECUTION_DRY_RUN=false")
            if not has_binance_creds:
                blocking.append("BINANCE_API_KEY/SECRET")
        if external_block:
            blocking.append(external_block)

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
                "venue": depth_venue,
                "bid_depth_usd": bid_depth,
                "ask_depth_usd": ask_depth,
                "fabricated": False,
                "secondary_l2_venues": secondary_l2_venues[:8],
                "book_walk": book_walk,
            },
            "order_venue": final.get("venue"),
            "fill_readiness": {
                "binance_testnet": testnet,
                "auto_execution_enabled": live_enabled,
                "dry_run_env": dry_env,
                "has_binance_creds": has_binance_creds,
                "live_path_armed": not dry_run,
                "order_host_probe": {
                    "ok": order_host_probe.get("ok"),
                    "geo_blocked": order_host_probe.get("geo_blocked"),
                    "external_block": order_host_probe.get("external_block"),
                    "hosts": order_host_probe.get("hosts"),
                },
                "external_block": external_block,
                "blocking": blocking,
            },
            "store": store_status(),
            "dry_run": effective_dry_run,
            "protocol_ack": protocol_ack,
            "proved_at": _utcnow(),
            "audit_trail": True,
            "verified_complete": bool(live_fill),
            "product_complete": False,
            "implementation_class": "VERIFIED_COMPLETE" if live_fill else "PARTIAL",
            "note": (
                "Live venue fill requires reachable Binance Spot Testnet order host + "
                "BINANCE_TESTNET + AUTO_EXECUTION_ENABLED + AUTO_EXECUTION_DRY_RUN=false + HMAC. "
                "HTTP 451 geo block is an external block — never claimed as live_fill. "
                "venue_protocol_proof is shape-only."
            ),
        }
    finally:
        if env_restore is not None:
            _arm_testnet_live_env(restore=env_restore)


def proof_status() -> dict[str, Any]:
    return {
        "surface": "venue_fill_proof",
        "modes": ["paper_lifecycle", "venue_protocol_proof", "testnet_live", "external_block_geo"],
        "live_fill_requires": [
            "BINANCE_TESTNET",
            "AUTO_EXECUTION_ENABLED",
            "AUTO_EXECUTION_DRY_RUN=false",
            "vault_or_test_creds",
            "reachable_testnet_order_host",
        ],
        "depth_source": "canonical_truth_bus_venue_l2",
        "paper_venue_follows_l2": True,
        "verified_complete": False,
        "implementation_class": "PARTIAL",
        "product_complete": False,
    }
