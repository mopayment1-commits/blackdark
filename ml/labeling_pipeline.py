"""
BLACKDARK — ML Labeling Flywheel (Phase 0).

Every oracle prediction is tracked, resolved at 1h/4h/24h horizons,
and exported as labeled training data for the AI model.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.MLLabeling")

Horizon = Literal["1h", "4h", "24h"]
HORIZON_HOURS = {"1h": 1, "4h": 4, "24h": 24}


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_asset(asset: str) -> str:
    cleaned = asset.upper().strip().replace("/", "").replace("-", "")
    if cleaned.endswith("USDT"):
        return cleaned[:-4]
    return cleaned


def score_verdict_accuracy(
    verdict: str,
    price_at: float,
    price_after: float,
) -> tuple[str, float, str]:
    """Return (outcome, accuracy_score, direction_label)."""
    if price_at <= 0 or price_after <= 0:
        return "unknown", 0.0, "flat"

    change_pct = ((price_after - price_at) / price_at) * 100
    if change_pct > 0.35:
        direction = "up"
    elif change_pct < -0.35:
        direction = "down"
    else:
        direction = "flat"

    verdict_upper = verdict.upper().replace("_", " ")
    buy_verdict = "BUY" in verdict_upper
    avoid_verdict = any(token in verdict_upper for token in ("AVOID", "TOUCH", "SELL", "WAIT"))

    if buy_verdict:
        if change_pct > 1.5:
            return "correct", min(100.0, 55.0 + change_pct * 4.0), direction
        if change_pct > -2.0:
            return "partial", max(35.0, 45.0 + change_pct * 5.0), direction
        return "incorrect", max(0.0, 25.0 + change_pct * 2.0), direction

    if avoid_verdict:
        if change_pct < -1.5:
            return "correct", min(100.0, 55.0 + abs(change_pct) * 4.0), direction
        if change_pct < 2.0:
            return "partial", max(35.0, 45.0 - change_pct * 5.0), direction
        return "incorrect", max(0.0, 25.0 - change_pct * 2.0), direction

    if abs(change_pct) <= 3.0:
        return "correct", min(100.0, 70.0 - abs(change_pct) * 3.0), direction
    return "partial", max(30.0, 50.0 - abs(change_pct) * 2.0), direction


async def fetch_reference_price(asset: str) -> float | None:
    pair = f"{_normalize_asset(asset)}USDT"
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={pair}"
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                payload = await resp.json()
        price = float(payload.get("price") or 0)
        return price if price > 0 else None
    except (aiohttp.ClientError, TypeError, ValueError):
        return None


def _prediction_age_hours(pred: dict[str, Any], now: datetime) -> float | None:
    raw_ts = str(pred.get("timestamp") or "")
    try:
        ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (now - ts).total_seconds() / 3600.0


async def resolve_mature_predictions(*, limit: int = 300) -> dict[str, Any]:
    from database import (
        fetch_unresolved_oracle_predictions,
        resolve_oracle_prediction,
        update_oracle_prediction_horizons,
    )

    unresolved = await fetch_unresolved_oracle_predictions(limit=limit)
    now = datetime.now(timezone.utc)
    resolved_count = 0
    partial_updates = 0

    for pred in unresolved:
        age_h = _prediction_age_hours(pred, now)
        if age_h is None:
            continue

        pred_id = int(pred["id"])
        asset = str(pred.get("asset") or "")
        price_at = float(pred.get("price_at_prediction") or 0)
        verdict = str(pred.get("verdict") or "")

        price_now = await fetch_reference_price(asset)
        if price_now is None:
            continue

        price_after_1h = float(pred.get("price_after_1h") or 0) or None
        price_after_4h = float(pred.get("price_after_4h") or 0) or None

        if age_h >= 1 and price_after_1h is None:
            await update_oracle_prediction_horizons(pred_id, price_after_1h=price_now)
            partial_updates += 1
            pred["price_after_1h"] = price_now

        if age_h >= 4 and price_after_4h is None:
            await update_oracle_prediction_horizons(pred_id, price_after_4h=price_now)
            partial_updates += 1
            pred["price_after_4h"] = price_now

        if age_h < HORIZON_HOURS["24h"]:
            continue

        outcome, accuracy, direction = score_verdict_accuracy(verdict, price_at, price_now)
        await resolve_oracle_prediction(
            pred_id,
            price_now,
            outcome,
            accuracy,
            price_after_1h=float(pred.get("price_after_1h") or price_now),
            price_after_4h=float(pred.get("price_after_4h") or price_now),
            label=outcome,
            direction_label=direction,
            resolved_at=_utcnow_iso(),
        )
        resolved_count += 1

    return {
        "checked": len(unresolved),
        "resolved_24h": resolved_count,
        "partial_horizon_updates": partial_updates,
        "timestamp": _utcnow_iso(),
    }


async def log_oracle_signal(
    *,
    asset: str,
    price: float,
    verdict: str,
    opportunity_score: float,
    confidence: float,
    kind: str | None = None,
    features: dict[str, Any] | None = None,
) -> int:
    from database import insert_oracle_prediction
    from ml.feature_store import build_feature_vector

    feature_payload = features or await build_feature_vector(asset, price_at=price)
    return await insert_oracle_prediction(
        asset=_normalize_asset(asset),
        price_at_prediction=price,
        verdict=verdict,
        opportunity_score=int(round(opportunity_score)),
        confidence=int(round(confidence)),
        kind=kind,
        features_json=json.dumps(feature_payload, separators=(",", ":")),
        source="oracle",
    )


async def export_labeled_dataset(*, limit: int = 5000) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions

    config.ML_TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    rows = await fetch_labeled_oracle_predictions(limit=limit)
    if not rows:
        return {"exported": 0, "path": None, "reason": "no_labeled_rows"}

    import pandas as pd

    frame = pd.DataFrame(rows)
    path = config.ML_TRAINING_DIR / "labeled_oracle_dataset.parquet"
    frame.to_parquet(path, index=False)
    return {
        "exported": len(rows),
        "path": str(path),
        "columns": list(frame.columns),
        "timestamp": _utcnow_iso(),
    }


async def run_labeling_flywheel_cycle() -> dict[str, Any]:
    from ml.experience_log import append_experience

    resolve_stats = await resolve_mature_predictions()
    export_stats = await export_labeled_dataset()
    train_stats: dict[str, Any] = {"trained": False, "reason": "auto_train_disabled"}
    if config.ML_AUTO_TRAIN:
        labeled_count = int(export_stats.get("exported") or 0)
        if labeled_count >= config.ML_MIN_TRAIN_SAMPLES:
            from ml.train_ensemble import train_direction_ensemble

            train_stats = await train_direction_ensemble()
        else:
            from ml.train_baseline import train_oracle_direction_model

            train_stats = await train_oracle_direction_model()
    payload = {
        "labeling": resolve_stats,
        "export": export_stats,
        "training": train_stats,
        "timestamp": _utcnow_iso(),
    }
    append_experience("flywheel_cycle", payload)
    return payload
