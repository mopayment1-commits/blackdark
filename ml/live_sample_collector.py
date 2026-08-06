"""
BLACKDARK — Live Oracle sample collector for the ML flywheel.

Logs current unified-oracle predictions with full feature vectors so the
training set accumulates real `arb_unified_v1` / `dashboard_unified_v1` rows.
"""

from __future__ import annotations

import logging
from typing import Any

import config

logger = logging.getLogger("BLACKDARK.LiveSampleCollector")


def _default_assets() -> list[str]:
    assets = sorted(getattr(config, "UNIVERSE_ASSETS", None) or {"BTC", "ETH", "SOL", "BNB", "XRP"})
    return [a.upper() for a in assets[:12]]


async def collect_live_unified_samples(
    assets: list[str] | None = None,
    *,
    include_ml: bool = True,
) -> dict[str, Any]:
    """Score live markets via unified Oracle and persist training samples."""
    from ml.labeling_pipeline import log_oracle_signal
    from oracle_unified import compute_unified_oracle

    target = [a.upper() for a in (assets or _default_assets())]
    logged = 0
    errors = 0
    details: list[dict[str, Any]] = []

    for asset in target:
        try:
            from market_context import fetch_binance_ticker

            market = await fetch_binance_ticker(f"{asset}USDT")
            if not market:
                errors += 1
                details.append({"asset": asset, "status": "no_market"})
                continue

            price = float(market.get("price") or 0)
            quote_volume = float(market.get("quote_volume") or market.get("quoteVolume") or 0)
            change = float(market.get("change_24h") or market.get("priceChangePercent") or 0)
            if price <= 0:
                errors += 1
                details.append({"asset": asset, "status": "bad_price"})
                continue

            unified = await compute_unified_oracle(
                asset,
                price,
                quote_volume,
                change,
                include_ml=include_ml,
            )
            pred_id = await log_oracle_signal(
                asset=asset,
                price=price,
                verdict=str(unified.get("verdict") or "NEUTRAL_OBSERVE"),
                opportunity_score=float(unified.get("opportunity_score") or 0),
                confidence=float(unified.get("confidence") or 0),
                kind="unified_live",
                source="dashboard_unified_v1",
                market_regime=str(unified.get("market_regime") or "neutral"),
            )
            logged += 1
            details.append(
                {
                    "asset": asset,
                    "status": "logged",
                    "prediction_id": pred_id,
                    "verdict": unified.get("verdict"),
                    "score": unified.get("opportunity_score"),
                }
            )
        except Exception:
            logger.exception("Live sample collect failed | asset=%s", asset)
            errors += 1
            details.append({"asset": asset, "status": "error"})

    return {
        "collected": logged,
        "errors": errors,
        "assets": target,
        "details": details,
        "source": "dashboard_unified_v1",
    }
