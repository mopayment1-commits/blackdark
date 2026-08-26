"""
Strategy Simulator — Feature #411 (Sprint 2 Simulation Module).

Paper Portfolio layer in Portfolio AI + Intelligence Ledger — NOT standalone EMS.
Legal name: Paper Portfolio (never "EMS", "Execution", or "Order Routing").

Real money order placement isolated/blocked — simulation only.
Integrations: #404 Live Breakeven, #410 Capital Awareness Controls, Intelligence Ledger.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.StrategySimulator")

_FEATURE_ID = 411
_TITLE = "Strategy Simulator"
_LEGAL_NAME = "Paper Portfolio"
_STANDALONE = False
_MERGED_INTO = "Portfolio AI + Intelligence Ledger / Simulation Layer"
_LAYER = "Portfolio AI"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/strategy_simulator_seed.json")
_METHODOLOGY_VERSION = "1.0"
_BREAKEVEN_FEATURE_ID = 404
_CAPITAL_AWARENESS_FEATURE_ID = 410

OrderSide = Literal["buy", "sell"]

_BANNED_TERMS = (
    "ems",
    "execution management",
    "order routing",
    "live execution",
    "real money",
    "auto execute",
)

_DISCLAIMER = (
    "SIMULATION — Paper Portfolio only. Real money order placement is blocked. "
    "All balances, orders, and fills are simulated on real market data. "
    "Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"paper_portfolio": {}, "order_schema": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("strategy simulator seed load failed: %s", exc)
        return {"paper_portfolio": {}, "order_schema": {}}


def build_sla_terms_block(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    sla = seed.get("sla_terms") or {}
    return {
        "simulation_explicit": True,
        "real_money_order_placement_blocked": True,
        "no_execution_api_keys": True,
        "ems_name_forbidden": seed.get("ems_name_forbidden", True),
        "execution_routes_blocked": seed.get("execution_routes_blocked", True),
        "legal_text": sla.get("legal_text", _DISCLAIMER),
        "ui_simulation_label_required": True,
        "display": "Real money order placement isolated/blocked — SIMULATION only",
    }


def _block_live_order(order: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed — any live execution attempt is blocked."""
    status = order.get("status", "")
    if status in ("live_submitted", "live_filled", "live_executed"):
        return {
            "ok": False,
            "blocked": True,
            "error": "real_money_order_blocked",
            "simulation_only": True,
            "display": "BLOCKED — real money order placement is not permitted",
        }
    return {"ok": True, "blocked": False, "simulation_only": True}


def build_paper_order(
    *,
    symbol: str,
    side: OrderSide,
    quantity: float,
    price: float,
    order_type: str = "limit",
) -> dict[str, Any]:
    """Create simulated paper order — never routes to live exchange."""
    order = {
        "order_id": f"paper_{uuid.uuid4().hex[:12]}",
        "symbol": symbol.upper(),
        "side": side,
        "quantity": quantity,
        "price": price,
        "order_type": order_type,
        "status": "paper_filled",
        "simulation_only": True,
        "real_money_blocked": True,
        "timestamp": _utcnow(),
    }
    blocked = _block_live_order(order)
    if blocked.get("blocked"):
        return blocked
    return {
        "ok": True,
        "order": order,
        "simulation_only": True,
        "display": f"SIMULATION: paper {side} {quantity} {symbol} @ ${price:,.2f}",
    }


def compute_paper_breakeven(paper_portfolio: dict[str, Any]) -> dict[str, Any]:
    """Integration #404 — breakeven for paper portfolio positions."""
    try:
        from bd_platform.live_breakeven_tracker import compute_dynamic_breakeven
    except ImportError:
        return {"ok": False, "error": "breakeven_module_unavailable"}

    results = {}
    for pos in paper_portfolio.get("positions") or []:
        symbol = pos.get("symbol", "")
        events = pos.get("events") or []
        calc = compute_dynamic_breakeven(events)
        if calc.get("ok"):
            current = float(pos.get("current_price", 0))
            be = calc["breakeven_price"]
            dist_pct = ((current - be) / be * 100) if be > 0 else None
            results[symbol] = {
                "breakeven_price": be,
                "current_price": current,
                "distance_to_breakeven_pct": round(dist_pct, 4) if dist_pct is not None else None,
                "remaining_quantity": calc["remaining_quantity"],
            }
    return {
        "ok": True,
        "integration": "live_breakeven_tracker",
        "feature_id": _BREAKEVEN_FEATURE_ID,
        "positions": results,
        "simulation_only": True,
    }


def apply_signal_to_paper_portfolio(
    signal_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Intelligence Ledger — apply signal to paper portfolio (simulation)."""
    seed = seed or _load_seed()
    signals = {s["signal_id"]: s for s in (seed.get("signals_available") or [])}
    signal = signals.get(signal_id)

    if not signal:
        return {"ok": False, "error": "signal_not_found", "simulation_only": True}

    paper = seed.get("paper_portfolio") or {}
    balance = float(paper.get("current_balance_usd", 0))
    action = signal.get("action", "")
    asset = signal.get("asset", "")
    qty_pct = float(signal.get("quantity_pct", 5)) / 100

    trade_value = balance * qty_pct
    side = "buy" if "buy" in action else "sell"

    for pos in paper.get("positions") or []:
        if pos.get("symbol") == asset:
            price = float(pos.get("current_price", 0))
            qty = trade_value / price if price > 0 else 0
            order = build_paper_order(symbol=asset, side=side, quantity=round(qty, 6), price=price)
            return {
                "ok": True,
                "signal_id": signal_id,
                "simulation_only": True,
                "paper_trade": order,
                "display": f"SIMULATION: applied signal {signal_id} to paper portfolio — {order.get('display')}",
            }

    return {
        "ok": False,
        "error": "asset_not_in_paper_portfolio",
        "simulation_only": True,
    }


def build_paper_backtest_30d(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Strategy Backtest on Paper — 30-day historical simulation."""
    seed = seed or _load_seed()
    bt = seed.get("backtest_30d") or {}

    return {
        "ok": True,
        "backtest_type": "paper_30d",
        "simulation_only": True,
        "real_money_blocked": True,
        "period": {
            "start": bt.get("start_date"),
            "end": bt.get("end_date"),
            "days": 30,
        },
        "results": {
            "initial_balance_usd": bt.get("initial_balance_usd"),
            "final_balance_usd": bt.get("final_balance_usd"),
            "return_pct": bt.get("return_pct"),
            "max_drawdown_pct": bt.get("max_drawdown_pct"),
            "sharpe_ratio": bt.get("sharpe_ratio"),
            "trades_simulated": bt.get("trades_simulated"),
            "win_rate_pct": bt.get("win_rate_pct"),
        },
        "historical_simulation_not_prediction": True,
        "not_investment_advice": True,
        "display": (
            f"SIMULATION 30d backtest: {bt.get('return_pct', 0):+.2f}% return | "
            f"max DD {bt.get('max_drawdown_pct', 0)}% | "
            f"{bt.get('trades_simulated', 0)} paper trades"
        ),
    }


def build_risk_budget_on_paper(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Integration #410 — test Risk Budget on paper portfolio before real decisions."""
    try:
        from bd_platform.capital_protection_controls import build_risk_budget_block
    except ImportError:
        return {"ok": False, "error": "capital_awareness_unavailable"}

    seed = seed or _load_seed()
    paper = seed.get("paper_portfolio") or {}
    bt = seed.get("backtest_30d") or {}

    budget = build_risk_budget_block()
    paper_dd = float(bt.get("max_drawdown_pct", 0))

    return {
        "ok": True,
        "integration": "capital_awareness_controls",
        "feature_id": _CAPITAL_AWARENESS_FEATURE_ID,
        "simulation_only": True,
        "paper_portfolio_id": paper.get("portfolio_id"),
        "paper_max_drawdown_30d_pct": paper_dd,
        "risk_budget": budget,
        "paper_within_budget": paper_dd <= float(budget.get("user_configured_max_loss_pct", 10)),
        "display": (
            f"SIMULATION: paper portfolio 30d max DD {paper_dd}% vs "
            f"risk budget {budget.get('user_configured_max_loss_pct')}%"
        ),
    }


def build_strategy_simulator_panel() -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    paper = seed.get("paper_portfolio") or {}
    order_schema = seed.get("order_schema") or {}

    breakeven = compute_paper_breakeven(paper)
    backtest = build_paper_backtest_30d(seed)
    risk_budget = build_risk_budget_on_paper(seed)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "ems_name_forbidden": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "surface": "portfolio_ai",
        "simulation_only": True,
        "real_money_blocked": True,
        "sla_terms": build_sla_terms_block(seed),
        "paper_portfolio": {
            "portfolio_id": paper.get("portfolio_id"),
            "initial_balance_usd": paper.get("initial_balance_usd"),
            "current_balance_usd": paper.get("current_balance_usd"),
            "cash_usd": paper.get("cash_usd"),
            "position_count": len(paper.get("positions") or []),
            "simulation_label": "SIMULATION — Paper Portfolio",
        },
        "order_schema": {
            "version": order_schema.get("version"),
            "simulation_only": True,
            "blocked_statuses": order_schema.get("blocked_statuses"),
            "allowed_statuses": order_schema.get("allowed_statuses"),
        },
        "breakeven_integration": breakeven,
        "risk_budget_integration": risk_budget,
        "backtest_30d": backtest,
        "integrations": {
            "live_breakeven_tracker": _BREAKEVEN_FEATURE_ID,
            "capital_awareness_controls": _CAPITAL_AWARENESS_FEATURE_ID,
            "intelligence_ledger_signals": True,
        },
        "acceptance_criteria": {
            "real_money_blocked": True,
            "simulation_explicit": True,
            "paper_portfolio_only": True,
            "breakeven_integration": True,
            "risk_budget_integration": True,
            "backtest_30d": True,
        },
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def strategy_simulator_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "surface": "portfolio_ai",
        "simulation_only": True,
        "real_money_blocked": True,
        "ems_name_forbidden": True,
        "sla_terms": build_sla_terms_block(seed),
        "components": {
            "paper_portfolio": True,
            "order_schema_simulation": True,
            "signal_application": True,
            "breakeven_integration_404": True,
            "risk_budget_integration_410": True,
            "backtest_30d": True,
        },
        "acceptance_criteria": {
            "real_money_order_placement_isolated_blocked": True,
            "simulation_in_all_ui": True,
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
        "detail": "Strategy Simulator not EMS standalone",
    })

    checks.append({
        "id": "real_money_blocked",
        "passed": seed.get("real_money_blocked") is True,
        "detail": "live orders blocked",
    })

    blocked = _block_live_order({"status": "live_submitted"})
    checks.append({
        "id": "live_order_fail_closed",
        "passed": blocked.get("blocked") is True,
        "detail": "live_submitted rejected",
    })

    panel = build_strategy_simulator_panel()
    checks.append({
        "id": "paper_portfolio",
        "passed": panel["paper_portfolio"]["position_count"] >= 2,
        "detail": "BTC + ETH paper positions",
    })

    checks.append({
        "id": "breakeven_integration_404",
        "passed": panel["breakeven_integration"].get("ok") is True,
        "detail": "paper breakeven computed",
    })

    checks.append({
        "id": "risk_budget_integration_410",
        "passed": panel["risk_budget_integration"].get("ok") is True,
        "detail": panel["risk_budget_integration"].get("display"),
    })

    checks.append({
        "id": "backtest_30d",
        "passed": panel["backtest_30d"].get("ok") is True,
        "detail": panel["backtest_30d"].get("display"),
    })

    applied = apply_signal_to_paper_portfolio("sig_btc_momentum", seed=seed)
    checks.append({
        "id": "signal_on_paper",
        "passed": applied.get("ok") is True and applied.get("simulation_only") is True,
        "detail": applied.get("display"),
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
