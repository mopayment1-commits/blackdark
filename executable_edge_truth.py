"""Canonical executable-edge honesty helpers.

No opportunity may be labeled profitable/executable unless depth + fees +
freshness support a positive NET EXECUTABLE PROFIT recomputed at decision time.
"""

from __future__ import annotations

from typing import Any


def mark_indicative_only(opportunity: dict[str, Any], *, reason: str) -> dict[str, Any]:
    """Downgrade optimistic labels to non-actionable indicative fields."""
    out = dict(opportunity)
    out["indicative"] = True
    out["indicative_reason"] = reason
    out["executable"] = False
    out["profitable"] = False
    out["actionable"] = False
    # Preserve topline for research, but never as execution claim.
    if "net_spread_bps" in out and "indicative_net_spread_bps" not in out:
        out["indicative_net_spread_bps"] = out.get("net_spread_bps")
    if "net_profit_usdt" in out and "indicative_net_profit_usdt" not in out:
        out["indicative_net_profit_usdt"] = out.get("net_profit_usdt")
    out["net_executable_profit_usdt"] = out.get("net_executable_profit_usdt")
    if out.get("net_executable_profit_usdt") is None:
        out["net_executable_profit_usdt"] = None
    return out


def apply_net_executable_profit(
    opportunity: dict[str, Any],
    *,
    net_profit_usdt: float | None,
    reason_if_none: str = "net_not_recomputed",
) -> dict[str, Any]:
    """Set profitable/executable from recomputed net only."""
    out = dict(opportunity)
    if net_profit_usdt is None:
        return mark_indicative_only(out, reason=reason_if_none)
    out["net_executable_profit_usdt"] = float(net_profit_usdt)
    out["net_profit_usdt"] = float(net_profit_usdt)
    positive = float(net_profit_usdt) > 0
    out["profitable"] = positive
    out["executable"] = positive and bool(out.get("executable", True))
    out["actionable"] = bool(out["executable"])
    out["indicative"] = not out["executable"]
    return out


async def enforce_execution_quote_truth(opportunity: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed stale + slip rewalk before any live/dry auto-exec path."""
    from stale_price_guard import validate_opportunity_quotes
    from slippage_guard import rewalk_opportunity_slippage

    ok, detail = validate_opportunity_quotes(opportunity, for_execution=True)
    if not ok:
        return {
            **mark_indicative_only(opportunity, reason="stale_or_invalid_quotes"),
            "stale_guard": detail,
            "cancel_reason": "stale_prices",
        }
    updated = await rewalk_opportunity_slippage(opportunity)
    if not updated.get("executable"):
        return mark_indicative_only(
            updated,
            reason=str(updated.get("cancel_reason") or updated.get("rewalk") or "not_executable"),
        )

    # Risk intelligence must influence execution gates (fail closed on blocks).
    from risk_intelligence import aggregate_risk_gate, liquidity_risk

    liq = liquidity_risk(
        symbol=str(updated.get("symbol") or ""),
        notional=float(updated.get("quote_amount") or updated.get("notional") or 0),
        bid_depth=updated.get("bid_depth"),
        ask_depth=updated.get("ask_depth"),
        spread_bps=updated.get("total_slippage_bps") or updated.get("spread_bps"),
    )
    # If depth fields absent but slip rewalk already passed, treat depth as verified via rewalk.
    if liq.get("reason") == "depth_unknown" and updated.get("executable"):
        liq = {
            **liq,
            "gate": "pass",
            "executable": True,
            "reason": "depth_verified_by_slip_rewalk",
        }
    gate = aggregate_risk_gate([liq])
    updated["risk_gate"] = gate
    if not gate.get("executable"):
        return mark_indicative_only(updated, reason="risk_gate_blocked")
    return updated
