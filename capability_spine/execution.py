"""Execution truth: slippage vector, liquidity, paper trading, reconciliation."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "capability_spine_execution_v1"


# ── CAP-03 Slippage Impact Vector ──────────────────────────────────────────────


def slippage_impact_vector(
    book: dict[str, Any],
    *,
    notional_usd: float,
    side: str = "buy",
    max_book_age_ms: float = 5000.0,
    book_age_ms: float | None = None,
) -> dict[str, Any]:
    """Multi-level book walk — top-of-book alone is insufficient."""
    if book_age_ms is not None and book_age_ms > max_book_age_ms:
        return {
            "ok": False,
            "reason": "stale_book",
            "book_age_ms": book_age_ms,
            "max_book_age_ms": max_book_age_ms,
            "methodology_version": METHODOLOGY_VERSION,
        }
    asks = book.get("asks") or []
    bids = book.get("bids") or []
    if not asks and not bids:
        return {"ok": False, "reason": "empty_book", "methodology_version": METHODOLOGY_VERSION}

    from arbitrage_engine import walk_asks, walk_bids

    mid = float(book.get("mid") or book.get("price") or 0)
    if side.lower() in {"buy", "long"}:
        result = walk_asks({"asks": asks, "bids": bids}, notional_usd)
        if result is None:
            return {
                "ok": False,
                "reason": "insufficient_depth",
                "notional_usd": notional_usd,
                "methodology_version": METHODOLOGY_VERSION,
            }
        slip_usd = notional_usd * result.slippage_bps / 10_000
        return {
            "ok": True,
            "side": side,
            "notional_usd": notional_usd,
            "expected_fill_price": round(result.average_price, 8),
            "slippage_bps": round(result.slippage_bps, 4),
            "slippage_usd": round(slip_usd, 4),
            "insufficient_depth": False,
            "levels_walked": result.levels_consumed,
            "book_age_ms": book_age_ms,
            "methodology_version": METHODOLOGY_VERSION,
        }

    base_qty = notional_usd / mid if mid > 0 else 0
    result = walk_bids({"asks": asks, "bids": bids}, base_qty)
    if result is None:
        return {
            "ok": False,
            "reason": "insufficient_depth",
            "notional_usd": notional_usd,
            "methodology_version": METHODOLOGY_VERSION,
        }
    slip_usd = notional_usd * result.slippage_bps / 10_000
    return {
        "ok": True,
        "side": side,
        "notional_usd": notional_usd,
        "expected_fill_price": round(result.average_price, 8),
        "slippage_bps": round(result.slippage_bps, 4),
        "slippage_usd": round(slip_usd, 4),
        "insufficient_depth": False,
        "levels_walked": result.levels_consumed,
        "book_age_ms": book_age_ms,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-39 Required-Size Liquidity Gate ─────────────────────────────────────────


def required_size_liquidity_gate(
    book: dict[str, Any],
    *,
    notional_usd: float,
    max_book_age_ms: float = 5000.0,
    book_age_ms: float | None = None,
) -> dict[str, Any]:
    vector = slippage_impact_vector(
        book,
        notional_usd=notional_usd,
        side="buy",
        max_book_age_ms=max_book_age_ms,
        book_age_ms=book_age_ms,
    )
    pass_gate = bool(vector.get("ok")) and not vector.get("insufficient_depth")
    return {
        "ok": True,
        "pass": pass_gate,
        "required_notional_usd": notional_usd,
        "executable_capacity_usd": notional_usd if pass_gate else 0.0,
        "slippage_vector": vector,
        "gate_state": "PASS" if pass_gate else "REJECT",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-40 Order-Book Integrity / Anti-Spoofing Gate ───────────────────────────


def order_book_integrity_gate(
    book_events: list[dict[str, Any]],
    *,
    burst_window_seconds: float = 5.0,
    cancel_velocity_threshold: float = 50.0,
) -> dict[str, Any]:
    from capability_spine.quant import order_cancellation_velocity

    cancel_metrics = order_cancellation_velocity(book_events, window_seconds=burst_window_seconds)
    velocity = float(cancel_metrics.get("velocity_per_second") or 0)
    spoof_like = cancel_metrics.get("ok") and velocity >= cancel_velocity_threshold
    return {
        "ok": True,
        "pass": not spoof_like,
        "spoof_like_pattern": bool(spoof_like),
        "cancellation_velocity": cancel_metrics,
        "threshold_per_second": cancel_velocity_threshold,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-49 Paper Trading Engine ────────────────────────────────────────────────


def paper_trading_execute(
    order: dict[str, Any],
    *,
    fill_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    model = fill_model or {}
    fees_bps = float(model.get("fees_bps") or 10.0)
    slip_bps = float(model.get("slippage_bps") or 5.0)
    latency_ms = float(model.get("latency_ms") or 50.0)
    qty = float(order.get("quantity") or 0)
    price = float(order.get("price") or 0)
    notional = qty * price
    filled = qty * float(model.get("fill_ratio") or 1.0)
    fees = notional * fees_bps / 10_000
    slip = notional * slip_bps / 10_000
    return {
        "ok": True,
        "mode": "PAPER",
        "order_id": order.get("order_id") or f"paper-{uuid.uuid4().hex[:12]}",
        "status": "FILLED" if filled >= qty else "PARTIAL",
        "filled_quantity": round(filled, 8),
        "fees_usd": round(fees, 4),
        "slippage_usd": round(slip, 4),
        "latency_ms": latency_ms,
        "real_money": False,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-51 Expected-vs-Simulated Execution Reconciliation ──────────────────────


def expected_vs_simulated_reconciliation(
    expected: dict[str, Any],
    simulated: dict[str, Any],
    *,
    tolerance_bps: float = 25.0,
) -> dict[str, Any]:
    exp_price = float(expected.get("expected_fill_price") or expected.get("price") or 0)
    sim_price = float(simulated.get("expected_fill_price") or simulated.get("fill_price") or 0)
    if exp_price <= 0 or sim_price <= 0:
        return {"ok": False, "reason": "missing_prices", "methodology_version": METHODOLOGY_VERSION}
    variance_bps = abs(sim_price - exp_price) / exp_price * 10_000
    within = variance_bps <= tolerance_bps
    return {
        "ok": True,
        "within_tolerance": within,
        "variance_bps": round(variance_bps, 4),
        "tolerance_bps": tolerance_bps,
        "reason": None if within else "price_variance_exceeds_tolerance",
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-52 Expected-vs-Observed Slippage Reconciliation ────────────────────────


def expected_vs_observed_slippage_reconciliation(
    expected_bps: float,
    observed_bps: float,
    *,
    tolerance_bps: float = 15.0,
    evidence_class: str = "LIVE_OBSERVATION",
) -> dict[str, Any]:
    if evidence_class in {"SIMULATED", "BACKTESTED", "PAPER"}:
        return {
            "ok": False,
            "reason": "observed_must_not_be_simulated_for_live_reconciliation",
            "methodology_version": METHODOLOGY_VERSION,
        }
    variance = abs(observed_bps - expected_bps)
    return {
        "ok": True,
        "within_tolerance": variance <= tolerance_bps,
        "expected_bps": expected_bps,
        "observed_bps": observed_bps,
        "variance_bps": round(variance, 4),
        "evidence_class": evidence_class,
        "methodology_version": METHODOLOGY_VERSION,
    }


# ── CAP-54 Executable Opportunity Ratio ────────────────────────────────────────


def executable_opportunity_ratio(
    opportunities: list[dict[str, Any]],
    *,
    version: str = "liquidity_gate_v1",
) -> dict[str, Any]:
    if not opportunities:
        return {"ok": False, "reason": "empty_sample", "methodology_version": METHODOLOGY_VERSION}
    executable = sum(1 for o in opportunities if o.get("executable") is True or o.get("gate_state") == "PASS")
    return {
        "ok": True,
        "numerator": executable,
        "denominator": len(opportunities),
        "ratio": round(executable / len(opportunities), 6),
        "gate_definition_version": version,
        "sample_size": len(opportunities),
        "methodology_version": METHODOLOGY_VERSION,
    }
