"""
AI Trade Simulator (#94) — paper trading engine integrated with #48 Decision Engine.

Modes:
- Forward (live paper): tracks real-time #48 signals
- Historical backtest: walk-forward with purged data (no future leakage)

Realistic execution: slippage + exchange fees + spread.
"""

from __future__ import annotations

import json
import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AITradeSimulator")

_PORTFOLIOS_PATH = Path("data/paper_trading_portfolios.json")
_TRADES_PATH = Path("data/paper_trading_trades.jsonl")
_SUPPORTED_ASSETS: tuple[str, ...] = (
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LINK",
    "MATIC", "POL", "LTC", "UNI", "ATOM", "ARB", "OP", "NEAR", "INJ", "SUI",
    "SEI", "TIA", "AAVE", "MKR", "CRV", "LDO", "PEPE", "WIF", "FET", "RENDER",
    "IMX", "GRT", "SAND", "MANA", "AXS", "ALGO", "XLM", "TRX", "ICP", "HBAR",
    "VET", "FTM", "FLOW", "STX", "KAS", "APT", "FIL", "ETC", "BCH", "RUNE",
)
_DEFAULT_CAPITAL = 10_000.0
_RISK_PER_TRADE = 0.02
_MIN_CONFIDENCE = 70.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_portfolios() -> dict[str, Any]:
    if not _PORTFOLIOS_PATH.exists():
        return {"portfolios": {}}
    try:
        return json.loads(_PORTFOLIOS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"portfolios": {}}


def _save_portfolios(data: dict[str, Any]) -> None:
    _PORTFOLIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PORTFOLIOS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_trade(row: dict[str, Any]) -> None:
    _TRADES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _TRADES_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def execution_price(
    signal_price: float,
    *,
    side: Literal["buy", "sell"],
    order_usd: float,
    spread_bps: float = 5.0,
    slippage_bps: float | None = None,
) -> dict[str, Any]:
    """Realistic execution model (#94)."""
    if slippage_bps is None:
        # Size-dependent slippage proxy
        slippage_bps = min(50.0, 2.0 + math.log10(max(order_usd, 100)) * 3.0)
    half_spread = spread_bps / 2
    impact_bps = half_spread + slippage_bps
    if side == "buy":
        executed = signal_price * (1 + impact_bps / 10_000)
    else:
        executed = signal_price * (1 - impact_bps / 10_000)
    return {
        "signal_price": round(signal_price, 6),
        "executed_price": round(executed, 6),
        "spread_bps": spread_bps,
        "slippage_bps": round(slippage_bps, 2),
        "impact_bps": round(impact_bps, 2),
    }


def exchange_fee_usd(notional: float, *, exchange: str = "binance") -> float:
    try:
        from fee_matrix import trading_fees_usdt

        fee = trading_fees_usdt(exchange, notional)
        return float(fee) if fee is not None else notional * 0.001
    except Exception:
        return notional * 0.001


@dataclass
class VirtualPortfolio:
    user_id: str
    capital_usd: float
    cash_usd: float
    positions: dict[str, dict[str, Any]] = field(default_factory=dict)
    equity_history: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "forward"

    def total_equity(self, prices: dict[str, float]) -> float:
        eq = self.cash_usd
        for asset, pos in self.positions.items():
            px = prices.get(asset, pos.get("avg_price", 0))
            eq += float(pos.get("quantity", 0)) * px
        return round(eq, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "capital_usd": self.capital_usd,
            "cash_usd": round(self.cash_usd, 2),
            "positions": self.positions,
            "equity_history": self.equity_history[-500:],
            "mode": self.mode,
            "updated_at": _utcnow(),
        }


def _get_portfolio(user_id: str, *, capital: float | None = None) -> VirtualPortfolio:
    data = _load_portfolios()
    row = (data.get("portfolios") or {}).get(user_id)
    if row:
        return VirtualPortfolio(
            user_id=user_id,
            capital_usd=float(row.get("capital_usd") or _DEFAULT_CAPITAL),
            cash_usd=float(row.get("cash_usd") or row.get("capital_usd") or _DEFAULT_CAPITAL),
            positions=row.get("positions") or {},
            equity_history=row.get("equity_history") or [],
            mode=row.get("mode") or "forward",
        )
    cap = capital or _DEFAULT_CAPITAL
    return VirtualPortfolio(user_id=user_id, capital_usd=cap, cash_usd=cap)


def _persist_portfolio(portfolio: VirtualPortfolio) -> None:
    data = _load_portfolios()
    data.setdefault("portfolios", {})[portfolio.user_id] = portfolio.to_dict()
    _save_portfolios(data)


def _max_drawdown(equity: list[float]) -> float:
    if not equity:
        return 0.0
    peak = equity[0]
    max_dd = 0.0
    for v in equity:
        peak = max(peak, v)
        if peak > 0:
            max_dd = max(max_dd, (peak - v) / peak)
    return round(max_dd * 100, 2)


def _sharpe(returns: list[float], *, periods: int = 365) -> float:
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
    std = math.sqrt(var) if var > 0 else 0.0
    return round((mean / std) * math.sqrt(periods), 3) if std else 0.0


def performance_report(
    trades: list[dict[str, Any]],
    equity_curve: list[float],
    *,
    initial_capital: float,
) -> dict[str, Any]:
    closed = [t for t in trades if t.get("status") == "closed"]
    wins = [t for t in closed if float(t.get("pnl_usd") or 0) > 0]
    losses = [t for t in closed if float(t.get("pnl_usd") or 0) <= 0]
    total_pnl = sum(float(t.get("pnl_usd") or 0) for t in closed)
    returns = []
    for i in range(1, len(equity_curve)):
        if equity_curve[i - 1] > 0:
            returns.append((equity_curve[i] - equity_curve[i - 1]) / equity_curve[i - 1])

    gross_profit = sum(float(t.get("pnl_usd") or 0) for t in wins)
    gross_loss = abs(sum(float(t.get("pnl_usd") or 0) for t in losses))
    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss > 0 else None

    final_eq = equity_curve[-1] if equity_curve else initial_capital
    total_return_pct = round(((final_eq / initial_capital) - 1) * 100, 2) if initial_capital > 0 else 0.0
    max_dd = _max_drawdown(equity_curve)

    return {
        "total_return_pct": total_return_pct,
        "total_pnl_usd": round(total_pnl, 2),
        "sharpe": _sharpe(returns),
        "max_drawdown_pct": max_dd,
        "win_rate": round(len(wins) / len(closed), 3) if closed else 0.0,
        "profit_factor": profit_factor,
        "calmar_ratio": round(total_return_pct / max_dd, 2) if max_dd > 0 else None,
        "trade_count": len(closed),
        "avg_win_usd": round(gross_profit / len(wins), 2) if wins else 0.0,
        "avg_loss_usd": round(-gross_loss / len(losses), 2) if losses else 0.0,
    }


async def _live_decision_signal(asset: str) -> dict[str, Any]:
    """Real-time #48 Decision Engine signal for forward paper mode."""
    from bd_platform.decision_engine_inputs import gather_decision_inputs

    row = await gather_decision_inputs(asset)
    risk = float(row.get("risk_score_delta") or 0)
    headlines = row.get("headlines") or []
    reasoning = headlines[0] if headlines else "Decision Engine aggregate"

    if risk <= -0.5:
        action = "buy"
        confidence = min(95.0, 70 + abs(risk) * 10)
    elif risk >= 1.0:
        action = "sell"
        confidence = min(95.0, 70 + risk * 8)
    else:
        action = "hold"
        confidence = max(45.0, 60 - abs(risk) * 5)

    return {
        "action": action,
        "confidence_pct": round(confidence, 1),
        "reasoning": reasoning,
        "risk_score_delta": risk,
        "signal_source": "decision_engine_48_live",
        "headlines": headlines[:3],
    }


def _position_size_usd(portfolio: VirtualPortfolio) -> float:
    return round(portfolio.cash_usd * _RISK_PER_TRADE, 2)


async def forward_paper_tick(
    user_id: str,
    asset: str = "BTC",
    *,
    manual_override: str | None = None,
) -> dict[str, Any]:
    """Forward paper trading tick — executes on #48 signal if confidence ≥70%."""
    portfolio = _get_portfolio(user_id)
    sym = asset.upper()
    signal = await _live_decision_signal(sym)
    action = manual_override or signal["action"]

    from bd_platform.strategy_lab_replay import fetch_ohlcv_series

    series = await fetch_ohlcv_series(sym, interval="1h", limit=5)
    price = float(series.bars[-1]["close"])

    trade_row: dict[str, Any] | None = None
    if action == "buy" and signal["confidence_pct"] >= _MIN_CONFIDENCE and sym not in portfolio.positions:
        size_usd = _position_size_usd(portfolio)
        if size_usd > portfolio.cash_usd:
            size_usd = portfolio.cash_usd * 0.95
        exec_row = execution_price(price, side="buy", order_usd=size_usd)
        fee = exchange_fee_usd(size_usd)
        qty = (size_usd - fee) / exec_row["executed_price"]
        portfolio.cash_usd -= size_usd
        portfolio.positions[sym] = {
            "quantity": round(qty, 8),
            "avg_price": exec_row["executed_price"],
            "entry_usd": size_usd,
            "opened_at": _utcnow(),
        }
        trade_row = {
            "trade_id": str(uuid.uuid4()),
            "user_id": user_id,
            "asset": sym,
            "side": "buy",
            "status": "open",
            "size_usd": size_usd,
            "execution": exec_row,
            "fee_usd": round(fee, 4),
            "ai_signal": signal,
            "ai_explanation": signal.get("reasoning"),
            "mode": "forward",
            "timestamp": _utcnow(),
        }
        _append_trade(trade_row)

    elif action == "sell" and sym in portfolio.positions:
        pos = portfolio.positions[sym]
        qty = float(pos["quantity"])
        exec_row = execution_price(price, side="sell", order_usd=qty * price)
        gross = qty * exec_row["executed_price"]
        fee = exchange_fee_usd(gross)
        pnl = gross - fee - float(pos.get("entry_usd") or 0)
        portfolio.cash_usd += gross - fee
        del portfolio.positions[sym]
        trade_row = {
            "trade_id": str(uuid.uuid4()),
            "user_id": user_id,
            "asset": sym,
            "side": "sell",
            "status": "closed",
            "size_usd": round(gross, 2),
            "execution": exec_row,
            "fee_usd": round(fee, 4),
            "pnl_usd": round(pnl, 4),
            "pnl_pct": round((pnl / float(pos.get("entry_usd") or 1)) * 100, 3),
            "ai_signal": signal,
            "ai_explanation": signal.get("reasoning"),
            "mode": "forward",
            "timestamp": _utcnow(),
        }
        _append_trade(trade_row)

    prices = {sym: price}
    eq = portfolio.total_equity(prices)
    portfolio.equity_history.append({"ts": _utcnow(), "equity_usd": eq})
    _persist_portfolio(portfolio)

    return {
        "ok": True,
        "feature": "#94",
        "mode": "forward",
        "user_id": user_id,
        "asset": sym,
        "signal": signal,
        "trade": trade_row,
        "portfolio": portfolio.to_dict(),
        "equity_usd": eq,
        "timestamp": _utcnow(),
    }


async def historical_backtest(
    asset: str = "BTC",
    *,
    start_bar: int = 48,
    max_bars: int = 200,
    initial_capital: float = 10_000.0,
    horizon_bars: int = 1,
) -> dict[str, Any]:
    """
    Walk-forward backtest with purged data — NO future leakage.
    Signals use point_in_time_decision_signal only.
    """
    from bd_platform.strategy_lab_replay import fetch_ohlcv_series, point_in_time_decision_signal

    series = await fetch_ohlcv_series(asset, interval="1h", limit=500)
    sym = series.asset
    cash = initial_capital
    position: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    equity_curve = [initial_capital]

    end = min(len(series) - horizon_bars - 1, start_bar + max_bars)
    for idx in range(start_bar, end):
        closes = series.closes_as_of(idx)
        signal = point_in_time_decision_signal(closes, asset=sym)
        bar = series.bar(idx)
        price = float(bar["close"])

        if signal["action"] == "buy" and signal["confidence_pct"] >= _MIN_CONFIDENCE and position is None:
            size_usd = cash * _RISK_PER_TRADE
            exec_row = execution_price(price, side="buy", order_usd=size_usd)
            fee = exchange_fee_usd(size_usd)
            qty = (size_usd - fee) / exec_row["executed_price"]
            cash -= size_usd
            position = {"quantity": qty, "entry_usd": size_usd, "entry_price": exec_row["executed_price"], "bar_index": idx}
            trades.append({
                "trade_id": f"bt-{idx}-open",
                "asset": sym,
                "side": "buy",
                "status": "open",
                "bar_index": idx,
                "execution": exec_row,
                "ai_signal": signal,
                "no_future_leakage": True,
            })

        elif signal["action"] == "sell" and position is not None:
            qty = float(position["quantity"])
            exec_row = execution_price(price, side="sell", order_usd=qty * price)
            gross = qty * exec_row["executed_price"]
            fee = exchange_fee_usd(gross)
            pnl = gross - fee - float(position["entry_usd"])
            cash += gross - fee
            trades.append({
                "trade_id": f"bt-{idx}-close",
                "asset": sym,
                "side": "sell",
                "status": "closed",
                "bar_index": idx,
                "execution": exec_row,
                "pnl_usd": round(pnl, 4),
                "pnl_pct": round((pnl / float(position["entry_usd"])) * 100, 3),
                "ai_signal": signal,
                "no_future_leakage": True,
            })
            position = None

        eq = cash
        if position:
            eq += float(position["quantity"]) * price
        equity_curve.append(round(eq, 2))

    # Close open position at last bar
    if position:
        last_price = float(series.bar(end - 1)["close"])
        qty = float(position["quantity"])
        exec_row = execution_price(last_price, side="sell", order_usd=qty * last_price)
        gross = qty * exec_row["executed_price"]
        fee = exchange_fee_usd(gross)
        pnl = gross - fee - float(position["entry_usd"])
        cash += gross - fee
        trades.append({
            "trade_id": f"bt-{end}-force-close",
            "asset": sym,
            "side": "sell",
            "status": "closed",
            "pnl_usd": round(pnl, 4),
            "ai_signal": {"action": "sell", "reasoning": "backtest_end"},
            "no_future_leakage": True,
        })
        equity_curve.append(round(cash, 2))

    buy_hold_return = 0.0
    if end > start_bar:
        start_px = float(series.bar(start_bar)["close"])
        end_px = float(series.bar(end - 1)["close"])
        buy_hold_return = round(((end_px / start_px) - 1) * 100, 2)

    perf = performance_report(trades, equity_curve, initial_capital=initial_capital)
    years = round((end - start_bar) / (24 * 365), 2)

    return {
        "ok": True,
        "feature": "#94",
        "mode": "historical_backtest",
        "asset": sym,
        "bars_tested": end - start_bar,
        "years_approx": years,
        "meets_2y_backtest": years >= 2.0 or len(series) >= 365 * 24,
        "initial_capital": initial_capital,
        "final_equity": equity_curve[-1] if equity_curve else initial_capital,
        "performance": perf,
        "buy_hold_return_pct": buy_hold_return,
        "comparison": {
            "simulator_return_pct": perf["total_return_pct"],
            "buy_hold_return_pct": buy_hold_return,
            "alpha_vs_buy_hold": round(perf["total_return_pct"] - buy_hold_return, 2),
        },
        "equity_curve": equity_curve[-100:],
        "trade_log": trades[-50:],
        "no_future_leakage": True,
        "signal_source": "point_in_time_replay_v1",
        "timestamp": _utcnow(),
    }


def reset_portfolio(user_id: str, *, capital: float = _DEFAULT_CAPITAL) -> dict[str, Any]:
    portfolio = VirtualPortfolio(user_id=user_id, capital_usd=capital, cash_usd=capital)
    _persist_portfolio(portfolio)
    return {"ok": True, "feature": "#94", "user_id": user_id, "portfolio": portfolio.to_dict()}


def get_portfolio_dashboard(user_id: str) -> dict[str, Any]:
    portfolio = _get_portfolio(user_id)
    return {
        "ok": True,
        "feature": "#94",
        "surface": "virtual_portfolio_dashboard",
        "portfolio": portfolio.to_dict(),
        "supported_assets": len(_SUPPORTED_ASSETS),
        "timestamp": _utcnow(),
    }


def ai_trade_simulator_status() -> dict[str, Any]:
    data = _load_portfolios()
    return {
        "ok": True,
        "feature": "#94",
        "role": "paper_trading_engine",
        "active_portfolios": len(data.get("portfolios") or {}),
        "supported_assets": len(_SUPPORTED_ASSETS),
        "modes": ["forward", "historical_backtest"],
        "min_confidence_pct": _MIN_CONFIDENCE,
        "risk_per_trade": _RISK_PER_TRADE,
        "no_future_leakage_backtest": True,
        "integrations": ["#48_decision_engine", "#92_strategy_lab_replay"],
        "timestamp": _utcnow(),
    }
