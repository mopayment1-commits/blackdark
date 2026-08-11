"""CEX↔DEX arbitrage execution — dry-run default, CEX live leg optional."""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.CexDexExecutor")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _dry_run_default() -> bool:
    if os.getenv("CEX_DEX_EXECUTION_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        return True
    return os.getenv("AUTO_EXECUTION_DRY_RUN", "true").lower() in {"1", "true", "yes"}


async def _dex_leg(
    asset: str,
    side: str,
    amount_usd: float,
    venue: str,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    """DEX leg via Jupiter product adapter (C4 cure) — dry-run default; live when wallet+flag."""
    from jupiter_dex_adapter import execute_swap

    return await execute_swap(
        asset=asset,
        side=side,
        amount_usd=amount_usd,
        venue=venue,
        dry_run=dry_run,
    )


async def _cex_leg(asset: str, side: str, amount_usd: float, *, dry_run: bool) -> dict[str, Any]:
    from execution_engine import execute_order

    return await execute_order(asset, "buy" if side == "buy" else "sell", amount_usd, dry_run=dry_run)


async def execute_cex_dex_opportunity(
    opportunity: dict[str, Any],
    *,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Two-leg CEX↔DEX execution: buy cheap venue, sell expensive venue."""
    from database import insert_execution_log

    use_dry = _dry_run_default() if dry_run is None else dry_run
    asset = str(opportunity.get("asset") or "BTC")
    quote_usd = float(opportunity.get("quote_usd") or os.getenv("CEX_DEX_QUOTE_USD", "500"))
    buy_venue = str(opportunity.get("buy_venue") or "binance").lower()
    sell_venue = str(opportunity.get("sell_venue") or "jupiter").lower()
    net_bps = float(opportunity.get("net_spread_bps") or 0)

    if net_bps < float(os.getenv("CEX_DEX_MIN_NET_BPS", "8")):
        return {"success": False, "skipped": True, "reason": "below_min_net_bps"}

    from execution_engine import get_execution_status

    status = await get_execution_status()
    if status.get("panic_active"):
        return {"success": False, "blocked": True, "reason": "panic_active"}

    legs: list[dict[str, Any]] = []

    if buy_venue in {"binance", "okx"}:
        legs.append(await _cex_leg(asset, "buy", quote_usd, dry_run=use_dry))
    else:
        legs.append(await _dex_leg(asset, "buy", quote_usd, buy_venue, dry_run=use_dry))

    if sell_venue in {"binance", "okx"}:
        legs.append(await _cex_leg(asset, "sell", quote_usd, dry_run=use_dry))
    else:
        legs.append(await _dex_leg(asset, "sell", quote_usd, sell_venue, dry_run=use_dry))

    live_any = any(leg.get("mode") == "live" and leg.get("executed") for leg in legs)
    result = {
        "timestamp": _utcnow(),
        "success": True,
        "asset": asset,
        "mode": "dry_run" if use_dry else "mixed",
        "net_spread_bps": net_bps,
        "estimated_profit_usd": opportunity.get("estimated_profit_usd"),
        "legs": legs,
        "why": opportunity.get("why"),
        "disclaimer": "DEX leg is simulated — CEX leg live only with Binance keys",
    }

    await insert_execution_log(
        "cex_dex",
        asset,
        json.dumps(result, default=str),
        live=live_any,
    )
    return result


async def run_cex_dex_cycle(
    *,
    quote_usd: float = 1000,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    from bd_platform.cex_dex_arbitrage import scan_cex_dex_opportunities

    scan = await scan_cex_dex_opportunities(quote_usd=quote_usd)
    opps = [o for o in scan.get("opportunities") or [] if o.get("profitable")]
    if not opps:
        return {"skipped": True, "reason": "no_profitable_cex_dex", "scan": scan}

    top = opps[0]
    if top.get("execution_feasibility") == "below_threshold":
        return {"skipped": True, "reason": "feasibility_low", "top": top}

    # Honor caller dry_run (HTTP forces safe dry-run); None → env default.
    exec_result = await execute_cex_dex_opportunity(top, dry_run=dry_run)
    return {"scan_count": scan.get("count"), "executed": exec_result, "dry_run": dry_run}


def cex_dex_status() -> dict[str, Any]:
    return {
        "timestamp": _utcnow(),
        "enabled": os.getenv("CEX_DEX_EXECUTION_ENABLED", "true").lower() in {"1", "true", "yes"},
        "auto_loop": os.getenv("CEX_DEX_AUTO_EXEC", "false").lower() in {"1", "true", "yes"},
        "dry_run_default": _dry_run_default(),
        "min_net_bps": float(os.getenv("CEX_DEX_MIN_NET_BPS", "8")),
        "quote_usd": float(os.getenv("CEX_DEX_QUOTE_USD", "500")),
        "scan_endpoint": "/api/platform/arb/cex-dex",
        "execute_endpoint": "/api/platform/arb/cex-dex/execute",
    }
