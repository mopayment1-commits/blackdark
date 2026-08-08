"""
BLACKDARK — Honest market-replay bootstrap for first model training.

Builds labeled samples from Binance hourly klines using point-in-time features
only (no future leakage). Tagged source=market_replay_v1 (trainable; not
historical_seed).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

import aiohttp

import config
from ml.labeling_pipeline import score_verdict_accuracy
from ml.training_utils import FEATURE_COLUMNS

logger = logging.getLogger("BLACKDARK.MarketReplayBootstrap")

DEFAULT_ASSETS = ("BTC", "ETH", "SOL", "BNB", "XRP")
SOURCE = "market_replay_v1"


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _returns_from_closes(closes: list[float]) -> dict[str, float]:
    if len(closes) < 2:
        return {"ret_1h": 0.0, "ret_4h": 0.0, "ret_24h": 0.0, "volatility": 0.0}
    last = closes[-1]
    ret_1h = (last / closes[-2] - 1.0) * 100 if len(closes) >= 2 else 0.0
    ret_4h = (last / closes[-5] - 1.0) * 100 if len(closes) >= 5 else ret_1h
    ret_24h = (last / closes[-25] - 1.0) * 100 if len(closes) >= 25 else ret_4h
    changes = [(closes[i] / closes[i - 1] - 1.0) * 100 for i in range(1, len(closes))]
    volatility = sum(abs(c) for c in changes[-24:]) / max(len(changes[-24:]), 1)
    return {
        "ret_1h": round(ret_1h, 4),
        "ret_4h": round(ret_4h, 4),
        "ret_24h": round(ret_24h, 4),
        "volatility": round(volatility, 4),
    }


def _verdict_from_past(closes: list[float]) -> str:
    """Point-in-time public taxonomy verdict — no future prices."""
    from regulatory_compliance_guard import to_public_verdict

    rets = _returns_from_closes(closes)
    ret_24h = rets["ret_24h"]
    vol = rets["volatility"]
    if vol > 2.5 and abs(ret_24h) > 4:
        return to_public_verdict("CAUTION")
    if ret_24h > 1.5:
        return to_public_verdict("BUY")
    if ret_24h < -1.5:
        return to_public_verdict("SELL")
    return to_public_verdict("WAIT")


def _feature_vector_from_closes(asset: str, closes: list[float]) -> dict[str, Any]:
    rets = _returns_from_closes(closes)
    price = float(closes[-1]) if closes else 0.0
    # Proxy microstructure / flow signals from returns only (point-in-time).
    mom = rets["ret_4h"]
    vol = max(rets["volatility"], 1e-6)
    obi_proxy = max(-1.0, min(1.0, mom / (vol * 3.0)))
    sentiment_proxy = max(-1.0, min(1.0, rets["ret_24h"] / 8.0))
    features = {
        "asset": asset,
        "price": round(price, 8),
        **rets,
        "sentiment_score": round(sentiment_proxy, 4),
        "sentiment_momentum": round(max(-1.0, min(1.0, rets["ret_1h"] / 3.0)), 4),
        "obi_score": round(obi_proxy * 5.0, 4),
        "obi_imbalance": round(obi_proxy, 4),
        "macro_weight": round(1.0 + max(-0.08, min(0.08, rets["ret_24h"] / 50.0)), 4),
        "funding_spread_bps": round(rets["ret_1h"] * 2.0, 4),
        "whale_sii": round(max(-8.0, min(8.0, rets["ret_4h"])), 4),
        "onchain_netflow": round(max(-10.0, min(10.0, -rets["ret_24h"] * 0.5)), 4),
    }
    # Ensure every training column exists.
    for col in FEATURE_COLUMNS:
        features.setdefault(col, 0.0)
    return features


async def _fetch_hourly_klines(
    session: aiohttp.ClientSession,
    asset: str,
    *,
    limit: int = 500,
) -> list[dict[str, Any]]:
    # api.binance.com may return 451 in restricted regions — use public mirrors.
    hosts = (
        "https://data-api.binance.vision",
        "https://api.binance.us",
        "https://api.binance.com",
    )
    params = {"symbol": f"{asset}USDT", "interval": "1h", "limit": limit}
    data: list[Any] = []
    for host in hosts:
        url = f"{host}/api/v3/klines"
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    continue
                payload = await resp.json()
                if isinstance(payload, list) and payload:
                    data = payload
                    break
        except (aiohttp.ClientError, TypeError, ValueError):
            continue
    rows: list[dict[str, Any]] = []
    for k in data:
        if not isinstance(k, list) or len(k) < 5:
            continue
        rows.append(
            {
                "ts": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
            }
        )
    return rows


async def bootstrap_market_replay_dataset(
    *,
    assets: list[str] | None = None,
    min_samples: int | None = None,
    lookback_hours: int = 480,
) -> dict[str, Any]:
    """
    Insert resolved market-replay samples until trainable volume is available.
    Skips work if enough non-synthetic labeled rows already exist.
    """
    from database import (
        fetch_labeled_oracle_predictions,
        init_db,
        insert_oracle_prediction,
        resolve_oracle_prediction,
    )

    await init_db()
    threshold = min_samples or max(int(config.ML_MIN_TRAIN_SAMPLES), 50)
    existing = await fetch_labeled_oracle_predictions(limit=threshold * 2, include_synthetic=False)
    if len(existing) >= threshold:
        return {
            "bootstrapped": False,
            "reason": "sufficient_labeled_samples",
            "existing_labeled": len(existing),
            "minimum_required": threshold,
        }

    target_assets = [a.upper() for a in (assets or list(DEFAULT_ASSETS))]
    inserted = 0
    resolved = 0
    correct = 0
    timeout = aiohttp.ClientTimeout(total=45)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for asset in target_assets:
            klines = await _fetch_hourly_klines(session, asset, limit=min(1000, lookback_hours + 48))
            if len(klines) < 48:
                logger.warning("Insufficient klines for bootstrap | asset=%s", asset)
                continue

            # Need 24h forward window for resolution.
            max_i = len(klines) - 25
            step = max(1, max_i // 40)
            for i in range(30, max_i, step):
                window = [row["close"] for row in klines[: i + 1]]
                price_at = float(klines[i]["close"])
                price_after = float(klines[i + 24]["close"])
                verdict = _verdict_from_past(window)
                features = _feature_vector_from_closes(asset, window)
                outcome, accuracy, direction = score_verdict_accuracy(
                    verdict, price_at, price_after
                )
                ts = datetime.fromtimestamp(klines[i]["ts"] / 1000, tz=UTC).isoformat()
                resolved_ts = datetime.fromtimestamp(
                    klines[i + 24]["ts"] / 1000, tz=UTC
                ).isoformat()
                score = min(95.0, max(35.0, 55.0 + features["ret_24h"]))
                conf = min(90.0, max(40.0, 60.0 - features["volatility"] * 3))

                pred_id = await insert_oracle_prediction(
                    asset=asset,
                    price_at_prediction=price_at,
                    verdict=verdict,
                    opportunity_score=round(score),
                    confidence=round(conf),
                    timestamp=ts,
                    kind="market_replay",
                    features_json=json.dumps(features, separators=(",", ":")),
                    source=SOURCE,
                )
                inserted += 1
                await resolve_oracle_prediction(
                    pred_id,
                    price_after,
                    outcome,
                    accuracy,
                    price_after_1h=float(klines[i + 1]["close"]),
                    price_after_4h=float(klines[i + 4]["close"]),
                    label=outcome,
                    direction_label=direction,
                    resolved_at=resolved_ts,
                )
                resolved += 1
                if outcome == "correct":
                    correct += 1

                if resolved >= threshold * 2:
                    break
            if resolved >= threshold * 2:
                break

    labeled = await fetch_labeled_oracle_predictions(limit=threshold * 3, include_synthetic=False)
    return {
        "bootstrapped": True,
        "source": SOURCE,
        "inserted": inserted,
        "resolved": resolved,
        "correct": correct,
        "hit_rate_percent": round((correct / resolved) * 100, 2) if resolved else 0.0,
        "trainable_labeled": len(labeled),
        "minimum_required": threshold,
        "timestamp": _utcnow_iso(),
        "note": "Point-in-time market replay — trainable, not historical_seed.",
    }
