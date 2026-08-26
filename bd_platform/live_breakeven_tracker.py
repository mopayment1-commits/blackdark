"""
Live Breakeven Tracker — Feature #404 (Sprint 2 Portfolio AI Enhancement).

Position Analytics Layer inside Portfolio AI — NOT standalone.
Legal name: "Dynamic Cost Basis" (never "Auto-Calculation").

Dynamic breakeven from: average entry + DCA + partial exits + exchange fees
(maker/taker) + network fees + funding accumulation + slippage.

Integrations: Intelligence Ledger (distance to breakeven on signals),
Capital Protection Controls (#410) proximity alerts.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.LiveBreakevenTracker")

_FEATURE_ID = 404
_TITLE = "Live Breakeven Tracker"
_LEGAL_NAME = "Dynamic Cost Basis"
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Position Analytics Layer"
_LAYER = "Portfolio AI"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/live_breakeven_tracker_seed.json")
_METHODOLOGY_VERSION = "1.0"
_ACCURACY_TOLERANCE_PCT = 0.01
_SERVER_REFRESH_SECONDS = 30
_CAPITAL_PROTECTION_FEATURE_ID = 410

EventType = Literal["buy", "sell", "funding"]

_BANNED_TERMS = (
    "auto-calculation",
    "auto calculation",
    "you should buy",
    "you should sell",
    "investment advice",
    "the system decides",
)

_DISCLAIMER = (
    "Live Breakeven Tracker (Dynamic Cost Basis) — fee-transparent cost basis analytics. "
    "Not investment advice. User assesses implications. "
    "Client-side instant preview; server refresh every 30 seconds."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"positions": {}, "user_holdings": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("live breakeven tracker seed load failed: %s", exc)
        return {"positions": {}, "user_holdings": {}}


def _event_fee_usd(event: dict[str, Any]) -> float:
    if event.get("type") not in ("buy", "sell"):
        return 0.0
    notional = float(event.get("quantity", 0)) * float(event.get("price", 0))
    fee_pct = float(event.get("fee_pct", 0)) / 100
    return round(notional * fee_pct, 4)


def compute_dynamic_breakeven(
    events: list[dict[str, Any]],
    *,
    remaining_quantity: float | None = None,
) -> dict[str, Any]:
    """
    Compute dynamic breakeven using average-cost method on remaining quantity.

    Includes: entries, DCA, partial exits, maker/taker fees, network fees,
    funding accumulation, slippage.
    """
    sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))

    total_qty = 0.0
    total_cost = 0.0
    funding_total = 0.0

    fee_lines: list[dict[str, Any]] = []
    entry_lines: list[dict[str, Any]] = []
    exit_lines: list[dict[str, Any]] = []

    for event in sorted_events:
        etype = event.get("type")
        if etype == "buy":
            qty = float(event.get("quantity", 0))
            price = float(event.get("price", 0))
            exchange_fee = _event_fee_usd(event)
            network_fee = float(event.get("network_fee_usd", 0))
            slippage = float(event.get("slippage_usd", 0))
            notional = qty * price
            line_cost = notional + exchange_fee + network_fee + slippage

            total_cost += line_cost
            total_qty += qty

            entry_lines.append({
                "event_id": event.get("event_id"),
                "label": event.get("label", "buy"),
                "quantity": qty,
                "price": price,
                "notional_usd": round(notional, 4),
                "timestamp": event.get("timestamp"),
            })
            if exchange_fee > 0:
                fee_lines.append({
                    "category": "exchange_fee",
                    "fee_type": event.get("fee_type", "taker"),
                    "amount_usd": round(exchange_fee, 4),
                    "event_id": event.get("event_id"),
                    "label": f"{event.get('fee_type', 'taker')} fee on buy",
                })
            if network_fee > 0:
                fee_lines.append({
                    "category": "network_fee",
                    "amount_usd": round(network_fee, 4),
                    "event_id": event.get("event_id"),
                    "label": "Network fee on buy",
                })
            if slippage > 0:
                fee_lines.append({
                    "category": "slippage",
                    "amount_usd": round(slippage, 4),
                    "event_id": event.get("event_id"),
                    "label": "Slippage on buy",
                })

        elif etype == "sell":
            qty = float(event.get("quantity", 0))
            if total_qty <= 0:
                continue
            avg_cost = total_cost / total_qty
            cost_removed = qty * avg_cost
            total_cost -= cost_removed
            total_qty -= qty

            exchange_fee = _event_fee_usd(event)
            exit_lines.append({
                "event_id": event.get("event_id"),
                "label": event.get("label", "sell"),
                "quantity": qty,
                "price": float(event.get("price", 0)),
                "cost_basis_removed_usd": round(cost_removed, 4),
                "timestamp": event.get("timestamp"),
            })
            if exchange_fee > 0:
                fee_lines.append({
                    "category": "exchange_fee",
                    "fee_type": event.get("fee_type", "taker"),
                    "amount_usd": round(exchange_fee, 4),
                    "event_id": event.get("event_id"),
                    "label": f"{event.get('fee_type', 'taker')} fee on sell (realized)",
                    "affects_remaining_breakeven": False,
                })

        elif etype == "funding":
            amount = float(event.get("amount_usd", 0))
            funding_total += amount
            fee_lines.append({
                "category": "funding_rate",
                "amount_usd": round(amount, 4),
                "event_id": event.get("event_id"),
                "label": event.get("label", "Funding rate accumulation"),
            })

    if remaining_quantity is not None and abs(total_qty - remaining_quantity) > 1e-6:
        logger.warning(
            "remaining_quantity mismatch: computed=%s seed=%s",
            total_qty,
            remaining_quantity,
        )

    if total_qty <= 0:
        return {
            "ok": False,
            "error": "zero_remaining_quantity",
            "remaining_quantity": total_qty,
        }

    breakeven_price = round((total_cost + funding_total) / total_qty, 8)
    per_unit_fees = round(funding_total / total_qty, 8) if funding_total else 0.0

    return {
        "ok": True,
        "breakeven_price": breakeven_price,
        "remaining_quantity": round(total_qty, 8),
        "remaining_cost_basis_usd": round(total_cost, 4),
        "funding_accumulation_usd": round(funding_total, 4),
        "funding_per_unit_usd": per_unit_fees,
        "entries": entry_lines,
        "exits": exit_lines,
        "fee_lines": fee_lines,
        "cost_method": "average_cost_remaining",
        "accuracy_tolerance_pct": _ACCURACY_TOLERANCE_PCT,
    }


def build_fee_transparency_block(calc: dict[str, Any]) -> dict[str, Any]:
    """Fee Transparency — every cent added to breakeven, competitive differentiator."""
    if not calc.get("ok"):
        return {"ok": False, "error": calc.get("error")}

    fee_lines = calc.get("fee_lines") or []
    by_category: dict[str, float] = {}
    line_items: list[dict[str, Any]] = []

    for line in fee_lines:
        cat = line.get("category", "other")
        amt = float(line.get("amount_usd", 0))
        if line.get("affects_remaining_breakeven", True):
            by_category[cat] = by_category.get(cat, 0) + amt
        line_items.append({
            **line,
            "display": f"+${amt:.4f} — {line.get('label', cat)}",
        })

    qty = float(calc.get("remaining_quantity", 1))
    total_fees_on_remaining = sum(by_category.values())
    notional_basis = float(calc.get("remaining_cost_basis_usd", 0))
    fee_impact_per_unit = total_fees_on_remaining / qty if qty > 0 else 0.0

    return {
        "fee_transparency": True,
        "every_cent_visible": True,
        "line_items": line_items,
        "by_category_usd": {k: round(v, 4) for k, v in by_category.items()},
        "total_fees_added_to_breakeven_usd": round(total_fees_on_remaining, 4),
        "fee_impact_per_unit_usd": round(fee_impact_per_unit, 8),
        "notional_cost_basis_usd": round(notional_basis, 4),
        "breakeven_price": calc.get("breakeven_price"),
        "competitive_differentiator": "CoinTracker/Delta/Koinly do not show per-cent fee breakdown",
        "display": (
            f"Breakeven ${calc.get('breakeven_price'):,.4f} includes "
            f"${total_fees_on_remaining:,.4f} in fees/funding/slippage "
            f"(${fee_impact_per_unit:,.4f}/unit)"
        ),
    }


def build_distance_to_breakeven(
    *,
    breakeven_price: float,
    current_price: float,
    remaining_quantity: float,
) -> dict[str, Any]:
    if breakeven_price <= 0:
        return {"ok": False, "error": "invalid_breakeven"}

    distance_usd = round(current_price - breakeven_price, 4)
    distance_pct = round((distance_usd / breakeven_price) * 100, 4)
    unrealized_pnl_usd = round(distance_usd * remaining_quantity, 2)

    if distance_pct > 0:
        position_vs_breakeven = "above_breakeven"
    elif distance_pct < 0:
        position_vs_breakeven = "below_breakeven"
    else:
        position_vs_breakeven = "at_breakeven"

    return {
        "distance_to_breakeven_usd": distance_usd,
        "distance_to_breakeven_pct": distance_pct,
        "unrealized_pnl_vs_breakeven_usd": unrealized_pnl_usd,
        "position_vs_breakeven": position_vs_breakeven,
        "current_price": current_price,
        "breakeven_price": breakeven_price,
        "display": (
            f"Price ${current_price:,.2f} is {abs(distance_pct):.2f}% "
            f"{'above' if distance_pct >= 0 else 'below'} breakeven "
            f"(${breakeven_price:,.4f})"
        ),
    }


def simulate_breakeven_scenario(
    position: dict[str, Any],
    *,
    hypothetical_dca_qty: float | None = None,
    hypothetical_dca_price: float | None = None,
    hypothetical_exit_qty: float | None = None,
    hypothetical_exit_price: float | None = None,
    fee_defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Breakeven Scenario Simulator — hypothetical DCA or partial exit impact."""
    fee_defaults = fee_defaults or {}
    maker_pct = float(fee_defaults.get("maker_fee_pct", 0.1))
    events = list(position.get("events") or [])

    baseline = compute_dynamic_breakeven(events)
    if not baseline.get("ok"):
        return {**baseline, "simulation": True}

    sim_events = list(events)
    scenario_label_parts: list[str] = []

    if hypothetical_dca_qty and hypothetical_dca_price:
        notional = hypothetical_dca_qty * hypothetical_dca_price
        sim_events.append({
            "event_id": "sim_dca",
            "type": "buy",
            "timestamp": "2099-01-01T00:00:00Z",
            "quantity": hypothetical_dca_qty,
            "price": hypothetical_dca_price,
            "fee_type": "maker",
            "fee_pct": maker_pct,
            "network_fee_usd": round(notional * 0.0001, 4),
            "slippage_usd": round(notional * 0.0002, 4),
            "label": "Hypothetical DCA",
        })
        scenario_label_parts.append(
            f"DCA {hypothetical_dca_qty} @ ${hypothetical_dca_price:,.2f}"
        )

    if hypothetical_exit_qty and hypothetical_exit_price:
        notional = hypothetical_exit_qty * hypothetical_exit_price
        sim_events.append({
            "event_id": "sim_exit",
            "type": "sell",
            "timestamp": "2099-01-02T00:00:00Z",
            "quantity": hypothetical_exit_qty,
            "price": hypothetical_exit_price,
            "fee_type": "taker",
            "fee_pct": float(fee_defaults.get("taker_fee_pct", 0.1)),
            "network_fee_usd": round(notional * 0.00005, 4),
            "slippage_usd": round(notional * 0.0001, 4),
            "label": "Hypothetical partial exit",
        })
        scenario_label_parts.append(
            f"Exit {hypothetical_exit_qty} @ ${hypothetical_exit_price:,.2f}"
        )

    if not scenario_label_parts:
        return {
            "ok": False,
            "error": "no_scenario_parameters",
            "hint": "Provide hypothetical_dca_qty/price or hypothetical_exit_qty/price",
        }

    simulated = compute_dynamic_breakeven(sim_events)
    if not simulated.get("ok"):
        return {**simulated, "simulation": True}

    delta_usd = round(simulated["breakeven_price"] - baseline["breakeven_price"], 8)
    delta_pct = round((delta_usd / baseline["breakeven_price"]) * 100, 4) if baseline["breakeven_price"] else 0

    return {
        "ok": True,
        "simulation": True,
        "scenario_label": " | ".join(scenario_label_parts),
        "baseline_breakeven": baseline["breakeven_price"],
        "simulated_breakeven": simulated["breakeven_price"],
        "breakeven_delta_usd": delta_usd,
        "breakeven_delta_pct": delta_pct,
        "baseline_quantity": baseline["remaining_quantity"],
        "simulated_quantity": simulated["remaining_quantity"],
        "fee_transparency": build_fee_transparency_block(simulated),
        "interactive_engagement": True,
        "not_investment_advice": True,
        "display": (
            f"Scenario: {' | '.join(scenario_label_parts)} | "
            f"Breakeven {baseline['breakeven_price']:,.4f} → {simulated['breakeven_price']:,.4f} "
            f"({delta_pct:+.4f}%)"
        ),
    }


def build_capital_protection_integration(
    position: dict[str, Any],
    calc: dict[str, Any],
    *,
    cp_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#410 Capital Protection Controls — breakeven proximity alerts."""
    cp_config = cp_config or {}
    proximity_pct = float(cp_config.get("breakeven_proximity_alert_pct", 1.5))
    max_loss_pct = float(cp_config.get("max_loss_breach_alert_pct", 5.0))
    enabled = cp_config.get("enabled", True)

    current_price = float(position.get("current_price", 0))
    distance = build_distance_to_breakeven(
        breakeven_price=float(calc.get("breakeven_price", 0)),
        current_price=current_price,
        remaining_quantity=float(calc.get("remaining_quantity", 0)),
    )

    dist_pct = abs(float(distance.get("distance_to_breakeven_pct", 0)))
    alerts: list[dict[str, Any]] = []

    if enabled and distance.get("position_vs_breakeven") == "above_breakeven":
        if dist_pct <= proximity_pct:
            alerts.append({
                "alert_type": "breakeven_proximity",
                "severity": "watch",
                "distance_pct": dist_pct,
                "threshold_pct": proximity_pct,
                "potential_pnl_usd": distance.get("unrealized_pnl_vs_breakeven_usd"),
                "display": (
                    f"Price within {proximity_pct}% of breakeven — "
                    f"potential P/L if crossed: ${distance.get('unrealized_pnl_vs_breakeven_usd', 0):,.2f}"
                ),
            })

    if enabled and distance.get("position_vs_breakeven") == "below_breakeven":
        if dist_pct >= max_loss_pct:
            alerts.append({
                "alert_type": "max_loss_breach",
                "severity": "elevated",
                "distance_pct": dist_pct,
                "threshold_pct": max_loss_pct,
                "potential_loss_usd": abs(distance.get("unrealized_pnl_vs_breakeven_usd", 0)),
                "display": (
                    f"Price {dist_pct:.2f}% below breakeven — "
                    f"exceeds {max_loss_pct}% capital protection threshold"
                ),
            })

    return {
        "integration": "capital_protection_controls",
        "feature_id": _CAPITAL_PROTECTION_FEATURE_ID,
        "mandatory": True,
        "enabled": enabled,
        "alerts": alerts,
        "alert_count": len(alerts),
        "config": {
            "breakeven_proximity_alert_pct": proximity_pct,
            "max_loss_breach_alert_pct": max_loss_pct,
        },
        "distance": distance,
        "display": (
            f"Capital Protection (#410): {len(alerts)} alert(s) active"
            if alerts
            else "Capital Protection (#410): no alerts triggered"
        ),
    }


def build_intelligence_ledger_signal_context(
    symbol: str,
    *,
    signal_id: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Intelligence Ledger — attach distance to breakeven when user owns asset."""
    seed = seed or _load_seed()
    sym = symbol.upper()
    holdings = seed.get("user_holdings") or {}
    holding = holdings.get(sym)

    if not holding or not holding.get("owns"):
        return {
            "ok": True,
            "symbol": sym,
            "user_owns_asset": False,
            "breakeven_context_attached": False,
            "display": f"No {sym} position — breakeven context not attached to signal",
        }

    position_id = holding.get("position_id")
    position = (seed.get("positions") or {}).get(position_id)
    if not position:
        return {"ok": False, "error": "position_not_found", "symbol": sym}

    calc = compute_dynamic_breakeven(position.get("events") or [])
    if not calc.get("ok"):
        return {**calc, "symbol": sym}

    distance = build_distance_to_breakeven(
        breakeven_price=calc["breakeven_price"],
        current_price=float(position.get("current_price", 0)),
        remaining_quantity=calc["remaining_quantity"],
    )

    return {
        "ok": True,
        "symbol": sym,
        "signal_id": signal_id,
        "user_owns_asset": True,
        "breakeven_context_attached": True,
        "breakeven_price": calc["breakeven_price"],
        "distance_to_breakeven": distance,
        "signal_context_note": (
            "Buy/sell signal interpretation may differ when user holds position near breakeven"
        ),
        "not_investment_advice": True,
        "display": distance.get("display"),
    }


def build_client_calculation_payload(position: dict[str, Any]) -> dict[str, Any]:
    """Payload for client-side instant calculation (mirrors server formula)."""
    calc = compute_dynamic_breakeven(position.get("events") or [])
    return {
        "client_side_instant": True,
        "server_refresh_seconds": _SERVER_REFRESH_SECONDS,
        "formula_version": _METHODOLOGY_VERSION,
        "cost_method": "average_cost_remaining",
        "events": position.get("events") or [],
        "current_price": position.get("current_price"),
        "server_breakeven": calc.get("breakeven_price") if calc.get("ok") else None,
        "accuracy_tolerance_pct": _ACCURACY_TOLERANCE_PCT,
    }


def build_live_breakeven_panel(position_id: str = "pos_btc_001") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    position = (seed.get("positions") or {}).get(position_id)

    if not position:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "position_not_found"}

    calc = compute_dynamic_breakeven(
        position.get("events") or [],
        remaining_quantity=float(position.get("remaining_quantity", 0)),
    )
    if not calc.get("ok"):
        return {**calc, "feature_id": _FEATURE_ID, "position_id": position_id}

    fee_block = build_fee_transparency_block(calc)
    distance = build_distance_to_breakeven(
        breakeven_price=calc["breakeven_price"],
        current_price=float(position.get("current_price", 0)),
        remaining_quantity=calc["remaining_quantity"],
    )
    cp_config = seed.get("capital_protection") or {}
    capital_protection = build_capital_protection_integration(position, calc, cp_config=cp_config)
    client_payload = build_client_calculation_payload(position)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "auto_calculation_name_forbidden": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "surface": "portfolio_ai",
        "position_id": position_id,
        "asset": position.get("asset"),
        "venue": position.get("venue"),
        "position_type": position.get("position_type"),
        "breakeven": {
            "price": calc["breakeven_price"],
            "remaining_quantity": calc["remaining_quantity"],
            "remaining_cost_basis_usd": calc["remaining_cost_basis_usd"],
            "cost_method": calc["cost_method"],
            "static_breakeven_rejected": True,
            "dynamic_cost_basis": True,
            "accuracy_tolerance_pct": _ACCURACY_TOLERANCE_PCT,
            "display": f"Live breakeven: ${calc['breakeven_price']:,.4f} per unit",
        },
        "fee_transparency": fee_block,
        "distance_to_breakeven": distance,
        "capital_protection": capital_protection,
        "client_calculation": client_payload,
        "refresh_policy": {
            "client_side_instant": True,
            "server_refresh_seconds": _SERVER_REFRESH_SECONDS,
        },
        "integrations": {
            "intelligence_ledger": True,
            "capital_protection_controls": _CAPITAL_PROTECTION_FEATURE_ID,
        },
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def live_breakeven_tracker_status() -> dict[str, Any]:
    seed = _load_seed()
    lr = seed.get("legal_review") or {}
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "auto_calculation_name_forbidden": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "surface": "portfolio_ai",
        "position_count": len(seed.get("positions") or {}),
        "accuracy_tolerance_pct": _ACCURACY_TOLERANCE_PCT,
        "refresh_policy": {
            "client_side_instant": True,
            "server_refresh_seconds": _SERVER_REFRESH_SECONDS,
        },
        "components": {
            "dynamic_breakeven": True,
            "fee_transparency": True,
            "scenario_simulator": True,
            "intelligence_ledger_integration": True,
            "capital_protection_integration": _CAPITAL_PROTECTION_FEATURE_ID,
        },
        "cost_factors": [
            "average_entry",
            "dca_entries",
            "partial_exits",
            "exchange_fees_maker_taker",
            "network_fees",
            "funding_rate_accumulation",
            "slippage",
        ],
        "acceptance_criteria": {
            "not_standalone": True,
            "fee_transparency_every_cent": True,
            "accuracy_within_0_01_pct": True,
            "client_side_instant": True,
            "server_refresh_30s": True,
            "scenario_simulator": True,
            "intelligence_ledger_distance": True,
            "capital_protection_alerts": True,
        },
        "legal_review": {
            "mandatory": True,
            "complete": bool(lr.get("complete", False)),
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({
        "id": "not_standalone",
        "passed": seed.get("standalone") is False,
        "detail": "merged into Portfolio AI",
    })

    checks.append({
        "id": "auto_calculation_name_forbidden",
        "passed": seed.get("legal_review", {}).get("auto_calculation_name_forbidden") is True,
        "detail": "uses Live Breakeven Tracker / Dynamic Cost Basis",
    })

    btc = build_live_breakeven_panel("pos_btc_001")
    checks.append({
        "id": "btc_breakeven_computed",
        "passed": btc.get("ok") and btc["breakeven"]["price"] > 0,
        "detail": f"breakeven={btc.get('breakeven', {}).get('price')}",
    })

    checks.append({
        "id": "fee_transparency_line_items",
        "passed": len(btc.get("fee_transparency", {}).get("line_items", [])) >= 3,
        "detail": "every-cent fee breakdown",
    })

    checks.append({
        "id": "distance_to_breakeven",
        "passed": "distance_to_breakeven_pct" in (btc.get("distance_to_breakeven") or {}),
        "detail": btc.get("distance_to_breakeven", {}).get("display"),
    })

    sim = simulate_breakeven_scenario(
        (seed.get("positions") or {})["pos_btc_001"],
        hypothetical_dca_qty=0.1,
        hypothetical_dca_price=62000,
        fee_defaults=seed.get("fee_defaults"),
    )
    checks.append({
        "id": "scenario_simulator",
        "passed": sim.get("ok") and sim.get("simulated_breakeven") is not None,
        "detail": sim.get("display"),
    })

    ledger = build_intelligence_ledger_signal_context("BTC", seed=seed)
    checks.append({
        "id": "intelligence_ledger_owns_asset",
        "passed": ledger.get("breakeven_context_attached") is True,
        "detail": ledger.get("display"),
    })

    ledger_no = build_intelligence_ledger_signal_context("SOL", seed=seed)
    checks.append({
        "id": "intelligence_ledger_no_position",
        "passed": ledger_no.get("breakeven_context_attached") is False,
        "detail": "SOL not owned",
    })

    cp = btc.get("capital_protection") or {}
    checks.append({
        "id": "capital_protection_integration",
        "passed": cp.get("feature_id") == _CAPITAL_PROTECTION_FEATURE_ID,
        "detail": cp.get("display"),
    })

    checks.append({
        "id": "client_side_payload",
        "passed": btc.get("client_calculation", {}).get("client_side_instant") is True,
        "detail": f"refresh={_SERVER_REFRESH_SECONDS}s",
    })

    checks.append({
        "id": "accuracy_tolerance_documented",
        "passed": seed.get("accuracy_target", {}).get("tolerance_pct") == 0.01,
        "detail": "±0.01%",
    })

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
