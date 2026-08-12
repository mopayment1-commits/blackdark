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
    # Recomputed net is authoritative for this helper. Callers that already
    # hard-blocked (executable=False + cancel_reason) should not invoke it.
    out["executable"] = positive
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
    return updated
