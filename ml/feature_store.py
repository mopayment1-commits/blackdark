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
        logger.debug("Local pricing unavailable | asset=%s", asset)
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


async def build_feature_vector(asset: str, *, price_at: float | None = None) -> dict[str, Any]:
    asset = _normalize_asset(asset)
    closes = await _recent_closes(asset)
    price = price_at or (closes[-1] if closes else 0.0)
    rets = _returns(closes)

    features: dict[str, Any] = {
        "asset": asset,
        "price": round(float(price or 0), 8),
        **rets,
        "universe_size_exchanges": len(config.INGESTION_READY_EXCHANGES),
        "universe_size_assets": len(config.UNIVERSE_ASSETS),
    }

    try:
        from sentiment_engine import get_sentiment_index_for_asset

        sentiment = await get_sentiment_index_for_asset(asset)
        features["sentiment_score"] = float(sentiment.get("compound_score") or 0)
        features["sentiment_momentum"] = float(sentiment.get("momentum") or 0)
    except Exception:
        features["sentiment_score"] = 0.0
        features["sentiment_momentum"] = 0.0

    try:
        from obi_predictor import get_obi_for_asset

        obi = await get_obi_for_asset(asset)
        features["obi_score"] = float(obi.get("score") or 0)
        features["obi_imbalance"] = float(obi.get("imbalance") or 0)
    except Exception:
        features["obi_score"] = 0.0
        features["obi_imbalance"] = 0.0

    try:
        from macro_correlations import macro_score_weight

        features["macro_weight"] = float(macro_score_weight() or 1.0)
    except Exception:
        features["macro_weight"] = 1.0

    return features
