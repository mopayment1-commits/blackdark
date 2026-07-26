"""Predictive liquidation radar — Binance free metrics + optional CoinGlass."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("BLACKDARK.LiquidationRadar")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


async def liquidation_radar(asset: str = "BTC") -> dict[str, Any]:
    from bd_platform.free_market_data import binance_liquidation_risk

    symbol = asset.upper()
    free = await binance_liquidation_risk(symbol)

    cg_alerts: list[dict[str, Any]] = []
    try:
        from bd_platform.derivatives_hub import derivatives_overview

        deriv = await derivatives_overview(symbol)
        cg = deriv.get("coinglass") or {}
        if (cg.get("liquidations") or {}).get("available"):
            cg_alerts.append({"type": "liquidation_cluster", "severity": "medium", "source": "coinglass"})
        if (cg.get("open_interest") or {}).get("available"):
            cg_alerts.append({"type": "oi_surge_watch", "severity": "low", "source": "coinglass"})
    except Exception as exc:
        logger.debug("CoinGlass radar supplement skipped: %s", exc)

    alerts = list(free.get("alerts") or []) + cg_alerts
    return {
        "asset": symbol,
        "timestamp": _utcnow(),
        "alerts": alerts,
        "metrics": free.get("metrics"),
        "data_source": free.get("data_source", "binance_futures_public"),
        "coinglass_supplement": bool(cg_alerts),
        "front_run_note": "Radar only — execution requires AUTO_EXECUTION + risk approval",
        "reference": "Insilico Terminal",
    }
