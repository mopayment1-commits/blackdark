"""
BLACKDARK — Feature Store for ML training.

Builds a compact feature vector per asset from local DB + data lake signals.
"""

from __future__ import annotations

import logging
from typing import Any

import config
logger = logging.getLogger("BLACKDARK.FeatureStore")


def _normalize_asset(asset: str) -> str:
    cleaned = asset.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4]
    return cleaned


async def _recent_closes(asset: str, *, limit: int = 48) -> list[float]:
    symbol = f"{_normalize_asset(asset)}/USDT"
    try:
        from database import fetch_recent_pricing_for_symbol

        rows = await fetch_recent_pricing_for_symbol(symbol, limit=limit)
        if len(rows) >= 5:
            return [float(row["price"]) for row in reversed(rows)]
    except Exception:
        logger.debug("Local pricing unavailable | asset=%s", str(asset).replace("\r", " ").replace("\n", " "))
    return []


def _returns(closes: list[float]) -> dict[str, float]:
    if len(closes) < 2:
        return {"ret_1h": 0.0, "ret_4h": 0.0, "ret_24h": 0.0, "volatility": 0.0}
    last = closes[-1]
    ret_1h = (last / closes[-2] - 1.0) * 100 if len(closes) >= 2 else 0.0
    ret_4h = (last / closes[-5] - 1.0) * 100 if len(closes) >= 5 else ret_1h
    ret_24h = (last / closes[0] - 1.0) * 100 if len(closes) >= 10 else ret_4h
    changes = [
        (closes[i] / closes[i - 1] - 1.0) * 100
        for i in range(1, len(closes))
    ]
    volatility = sum(abs(c) for c in changes[-24:]) / max(len(changes[-24:]), 1)
    return {
        "ret_1h": round(ret_1h, 4),
        "ret_4h": round(ret_4h, 4),
        "ret_24h": round(ret_24h, 4),
        "volatility": round(volatility, 4),
    }


async def _sentiment_features(asset: str) -> tuple[float, float]:
    """Return (compound_score, momentum) from rolling indices when available."""
    try:
        from sentiment_engine import get_rolling_compound_sentiment_index

        compound = float(await get_rolling_compound_sentiment_index(asset))
    except Exception:
        logger.debug("Sentiment feature unavailable | asset=%s", str(asset).replace("\r", " ").replace("\n", " "), exc_info=True)
        compound = 0.0

    momentum = 0.0
    try:
        from database import fetch_rolling_compound_sentiment_index

        # Prefer a shorter window as a momentum proxy when DB helper exists.
        short = float(
            await fetch_rolling_compound_sentiment_index(
                asset,
                window_seconds=max(60, int(getattr(config, "SENTIMENT_ROLLING_WINDOW_SECONDS", 300) // 3)),
            )
        )
        momentum = round(short - compound, 4)
    except Exception:
        momentum = round(compound * 0.25, 4)

    return round(compound, 4), momentum


async def _obi_features(asset: str) -> tuple[float, float]:
    """Return (obi_score_adjustment-like, imbalance) from live/DB books."""
    try:
        from database import fetch_latest_order_books
        from obi_predictor import build_obi_context_safe, get_obi_for_asset, obi_score_adjustment_for_asset

        books = await fetch_latest_order_books()
        ctx = await build_obi_context_safe(books)
        imbalance = get_obi_for_asset(asset, ctx)
        score = obi_score_adjustment_for_asset(asset, ctx)
        return float(score or 0.0), float(imbalance or 0.0)
    except Exception:
        logger.debug("OBI feature unavailable | asset=%s", str(asset).replace("\r", " ").replace("\n", " "), exc_info=True)
        return 0.0, 0.0


async def _macro_weight() -> float:
    try:
        from macro_correlations import get_latest_macro_regime, macro_score_weight

        ctx = await get_latest_macro_regime()
        return float(macro_score_weight(ctx) or 1.0)
    except Exception:
        logger.debug("Macro feature unavailable", exc_info=True)
        return 1.0


async def _funding_spread_bps(asset: str) -> float:
    try:
        from database import fetch_latest_funding_rates

        books = await fetch_latest_funding_rates()
        rates: list[float] = []
        target = _normalize_asset(asset)
        for symbols in (books or {}).values():
            for symbol, payload in (symbols or {}).items():
                cleaned = str(symbol).upper().replace("/", "").replace("-", "")
                if cleaned.startswith(target):
                    rates.append(float((payload or {}).get("funding_rate") or 0.0) * 10_000.0)
        if len(rates) >= 2:
            return round(max(rates) - min(rates), 4)
        if rates:
            return round(rates[0], 4)
    except Exception:
        logger.debug("Funding feature unavailable | asset=%s", str(asset).replace("\r", " ").replace("\n", " "), exc_info=True)
    return 0.0


async def _whale_sii(asset: str) -> float:
    try:
        from whale_tracker import get_latest_institutional_context, whale_score_boost_for_asset

        ctx = await get_latest_institutional_context()
        return round(float(whale_score_boost_for_asset(asset, ctx) or 0.0), 4)
    except Exception:
        logger.debug("Whale SII feature unavailable | asset=%s", str(asset).replace("\r", " ").replace("\n", " "), exc_info=True)
        return 0.0


async def _onchain_netflow(asset: str) -> float:
    try:
        from onchain_tracker import (
            build_onchain_context_safe,
            get_onchain_status_for_asset,
            onchain_score_adjustment_for_asset,
        )

        ctx = await build_onchain_context_safe()
        status = get_onchain_status_for_asset(asset, ctx) or {}
        for key in ("netflow_usd", "net_flow_usd", "exchange_netflow"):
            if status.get(key) is not None:
                return round(float(status[key]), 4)
        return round(float(onchain_score_adjustment_for_asset(asset, ctx) or 0.0), 4)
    except Exception:
        logger.debug("On-chain feature unavailable | asset=%s", str(asset).replace("\r", " ").replace("\n", " "), exc_info=True)
        return 0.0


async def build_feature_vector(asset: str, *, price_at: float | None = None) -> dict[str, Any]:
    asset = _normalize_asset(asset)
    closes = await _recent_closes(asset)
    price = price_at or (closes[-1] if closes else 0.0)
    rets = _returns(closes)
    sentiment_score, sentiment_momentum = await _sentiment_features(asset)
    obi_score, obi_imbalance = await _obi_features(asset)
    macro_weight = await _macro_weight()
    funding_spread_bps = await _funding_spread_bps(asset)
    whale_sii = await _whale_sii(asset)
    onchain_netflow = await _onchain_netflow(asset)

    return {
        "asset": asset,
        "price": round(float(price or 0), 8),
        **rets,
        "universe_size_exchanges": len(config.INGESTION_READY_EXCHANGES),
        "universe_size_assets": len(config.UNIVERSE_ASSETS),
        "sentiment_score": sentiment_score,
        "sentiment_momentum": sentiment_momentum,
        "obi_score": round(obi_score, 4),
        "obi_imbalance": round(obi_imbalance, 4),
        "macro_weight": round(macro_weight, 4),
        "funding_spread_bps": funding_spread_bps,
        "whale_sii": whale_sii,
        "onchain_netflow": onchain_netflow,
    }
