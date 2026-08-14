"""
BLACKDARK — ML Labeling Flywheel (Phase 0).

Every oracle prediction is tracked, resolved at 1h/4h/24h horizons,
and exported as labeled training data for the AI model.
"""

from __future__ import annotations

import asyncio

import json
import logging
from datetime import UTC, datetime
from typing import Any, Literal

import aiohttp

import config

logger = logging.getLogger("BLACKDARK.MLLabeling")

Horizon = Literal["1h", "4h", "24h"]
HORIZON_HOURS = {"1h": 1, "4h": 4, "24h": 24}


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


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
    from regulatory_compliance_guard import classify_internal_verdict

    bucket = classify_internal_verdict(verdict)
    if bucket == "unknown":
        return "abstain", 0.0, "flat"
    outcome, score = _score_change_for_bucket(bucket, change_pct)
    return outcome, score, _direction_from_change(change_pct)


def _direction_from_change(change_pct: float) -> str:
    if change_pct > 0.35:
        return "up"
    if change_pct < -0.35:
        return "down"
    return "flat"


def _score_change_for_bucket(bucket: str, change_pct: float) -> tuple[str, float]:
    if bucket == "bullish":
        return _score_bullish_change(change_pct)
    if bucket in {"bearish", "risk"}:
        return _score_avoid_change(change_pct)
    return _score_neutral_change(change_pct)


def _score_bullish_change(change_pct: float) -> tuple[str, float]:
    if change_pct > 1.5:
        return "correct", min(100.0, 55.0 + change_pct * 4.0)
    if change_pct > -2.0:
        return "partial", max(35.0, 45.0 + change_pct * 5.0)
    return "incorrect", max(0.0, 25.0 + change_pct * 2.0)


def _score_avoid_change(change_pct: float) -> tuple[str, float]:
    if change_pct < -1.5:
        return "correct", min(100.0, 55.0 + abs(change_pct) * 4.0)
    if change_pct < 2.0:
        return "partial", max(35.0, 45.0 - change_pct * 5.0)
    return "incorrect", max(0.0, 25.0 - change_pct * 2.0)


def _score_neutral_change(change_pct: float) -> tuple[str, float]:
    if abs(change_pct) <= 3.0:
        return "correct", min(100.0, 70.0 - abs(change_pct) * 3.0)
    return "partial", max(30.0, 50.0 - abs(change_pct) * 2.0)


async def fetch_reference_price(asset: str) -> float | None:
    pair = f"{_normalize_asset(asset)}USDT"
    hosts = (
        "https://data-api.binance.vision",
        "https://api.binance.us",
        "https://api.binance.com",
    )
    timeout = aiohttp.ClientTimeout(total=10)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            for host in hosts:
                url = f"{host}/api/v3/ticker/price?symbol={pair}"
                try:
                    async with session.get(url) as resp:
                        if resp.status != 200:
                            continue
                        payload = await resp.json()
                    price = float(payload.get("price") or 0)
                    if price > 0:
                        return price
                except (aiohttp.ClientError, TypeError, ValueError):
                    continue
    except (aiohttp.ClientError, TypeError, ValueError):
        return None
    return None


def _prediction_age_hours(pred: dict[str, Any], now: datetime) -> float | None:
    raw_ts = str(pred.get("timestamp") or "")
    try:
        ts = datetime.fromisoformat(raw_ts)
    except ValueError:
        return None
    return (now - ts).total_seconds() / 3600.0


async def _stamp_mature_horizon_prices(
    pred: dict[str, Any],
    pred_id: int,
    age_h: float,
    price_now: float,
) -> int:
    from database import update_oracle_prediction_horizons

    updates = 0
    price_after_1h = float(pred.get("price_after_1h") or 0) or None
    price_after_4h = float(pred.get("price_after_4h") or 0) or None
    if 1 <= age_h < 2.5 and price_after_1h is None:
        await update_oracle_prediction_horizons(pred_id, price_after_1h=price_now)
        pred["price_after_1h"] = price_now
        updates += 1
    if 4 <= age_h < 6 and price_after_4h is None:
        await update_oracle_prediction_horizons(pred_id, price_after_4h=price_now)
        pred["price_after_4h"] = price_now
        updates += 1
    return updates


async def _resolve_prediction_24h(pred: dict[str, Any], pred_id: int, price_now: float) -> None:
    from database import resolve_oracle_prediction

    price_at = float(pred.get("price_at_prediction") or 0)
    verdict = str(pred.get("verdict") or "")
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
    await _resolve_registry_label(pred, pred_id, outcome, accuracy, direction, price_now)


async def _resolve_registry_label(
    pred: dict[str, Any],
    pred_id: int,
    outcome: str,
    accuracy: float,
    direction: str,
    price_now: float,
) -> None:
    await asyncio.sleep(0)
    try:
        from signal_registry import list_signals, resolve_signal

        meta = {
            "accuracy": accuracy,
            "direction_label": direction,
            "price_after": price_now,
            "resolved_via": "labeling_pipeline",
        }
        resolved = resolve_signal(str(pred_id), str(outcome), meta=meta)
        if not resolved:
            _backfill_registry_label(pred, pred_id, outcome, meta, list_signals, resolve_signal)
    except Exception:
        pass


def _backfill_registry_label(
    pred: dict[str, Any],
    pred_id: int,
    outcome: str,
    meta: dict[str, Any],
    list_signals: Any,
    resolve_signal: Any,
) -> None:
    asset_u = str(pred.get("asset") or "").upper()
    for row in list_signals(limit=40, asset=asset_u or None, unlabeled_only=True):
        if str(row.get("prediction_id") or "") not in {"", "None", "null"}:
            continue
        resolve_signal(
            str(row.get("signal_id")),
            str(outcome),
            meta={
                **meta,
                "resolved_via": "labeling_backfill_asset",
                "matched_prediction_id": pred_id,
            },
        )
        break


async def resolve_mature_predictions(*, limit: int = 300) -> dict[str, Any]:
    from database import fetch_unresolved_oracle_predictions

    unresolved = await fetch_unresolved_oracle_predictions(limit=limit)
    now = datetime.now(UTC)
    resolved_count = 0
    partial_updates = 0

    for pred in unresolved:
        age_h = _prediction_age_hours(pred, now)
        if age_h is None:
            continue

        pred_id = int(pred["id"])
        asset = str(pred.get("asset") or "")

        price_now = await fetch_reference_price(asset)
        if price_now is None:
            continue

        partial_updates += await _stamp_mature_horizon_prices(pred, pred_id, age_h, price_now)

        if age_h < HORIZON_HOURS["24h"]:
            continue

        await _resolve_prediction_24h(pred, pred_id, price_now)
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
    source: str = "oracle",
    market_regime: str | None = None,
) -> int:
    from database import insert_oracle_prediction
    from ml.feature_store import build_feature_vector

    feature_payload = features or await build_feature_vector(asset, price_at=price)
    regime = market_regime
    if not regime and isinstance(feature_payload, dict):
        regime = feature_payload.get("market_regime") or feature_payload.get("regime")
    return await insert_oracle_prediction(
        asset=_normalize_asset(asset),
        price_at_prediction=price,
        verdict=verdict,
        opportunity_score=round(opportunity_score),
        confidence=round(confidence),
        kind=kind,
        features_json=json.dumps(feature_payload, separators=(",", ":")),
        source=source or "oracle",
        market_regime=str(regime or "neutral"),
    )


async def export_labeled_dataset(*, limit: int = 5000) -> dict[str, Any]:
    from database import fetch_labeled_oracle_predictions

    config.ML_TRAINING_DIR.mkdir(parents=True, exist_ok=True)
    rows = await fetch_labeled_oracle_predictions(limit=limit, include_synthetic=False)
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


async def _collect_live_samples_if_enabled(collect_live: bool) -> dict[str, Any]:
    if not collect_live:
        return {"collected": 0, "skipped": True}
    try:
        from ml.live_sample_collector import collect_live_unified_samples

        return await collect_live_unified_samples()
    except Exception:
        logger.exception("Live sample collection failed")
        return {"collected": 0, "error": "collect_failed"}


async def _bootstrap_market_replay_if_needed(bootstrap_if_needed: bool) -> dict[str, Any]:
    if not bootstrap_if_needed:
        return {"bootstrapped": False}
    try:
        from database import fetch_labeled_oracle_predictions
        from ml.market_replay_bootstrap import bootstrap_market_replay_dataset

        labeled = await fetch_labeled_oracle_predictions(
            limit=config.ML_MIN_TRAIN_SAMPLES,
            include_synthetic=False,
        )
        if len(labeled) < config.ML_MIN_TRAIN_SAMPLES:
            return await bootstrap_market_replay_dataset()
    except Exception:
        logger.exception("Market replay bootstrap failed")
        return {"bootstrapped": False, "error": "bootstrap_failed"}
    return {"bootstrapped": False}


async def _drift_monitoring_stats(export_stats: dict[str, Any], bootstrap_stats: dict[str, Any]) -> dict[str, Any]:
    if int(export_stats.get("exported") or 0) < 10:
        return {"drift_detected": False}
    try:
        from database import fetch_labeled_oracle_predictions
        from ml.drift_monitor import drift_report, enforce_drift_actions
        from ml.feature_store import build_feature_vector

        labeled_rows = await fetch_labeled_oracle_predictions(limit=500, include_synthetic=False)
        replay_share = _replay_share(labeled_rows)
        recent_features = [
            await build_feature_vector(str(row.get("asset") or "BTC"))
            for row in labeled_rows[-20:]
        ]
        drift_stats = drift_report(labeled_rows, recent_features)
        if replay_share >= 0.5 or bootstrap_stats.get("bootstrapped"):
            drift_stats["enforcement"] = {
                "action": "skip_freeze_bootstrap_mix",
                "replay_share": round(replay_share, 3),
            }
        else:
            drift_stats["enforcement"] = enforce_drift_actions(drift_stats)
        return drift_stats
    except Exception:
        logger.exception("Drift monitoring cycle failed")
        return {"drift_detected": False}


def _replay_share(labeled_rows: list[dict[str, Any]]) -> float:
    if not labeled_rows:
        return 0.0
    replay_count = sum(1 for row in labeled_rows if str(row.get("source") or "") == "market_replay_v1")
    return replay_count / len(labeled_rows)


async def _train_direction_model_if_enabled(export_stats: dict[str, Any]) -> dict[str, Any]:
    if not config.ML_AUTO_TRAIN:
        return {"trained": False, "reason": "auto_train_disabled"}
    labeled_count = int(export_stats.get("exported") or 0)
    if labeled_count >= config.ML_MIN_TRAIN_SAMPLES:
        from ml.train_ensemble import train_direction_ensemble

        train_stats = await train_direction_ensemble()
        if train_stats.get("trained"):
            return train_stats
    from ml.train_baseline import train_oracle_direction_model

    return await train_oracle_direction_model()


async def _train_regime_models_safe() -> dict[str, Any]:
    try:
        from ml.train_regime_models import train_regime_models

        return await train_regime_models(force=False)
    except Exception:
        logger.exception("Regime model training cycle failed")
        return {"trained": False, "error": "regime_train_failed"}


async def _backfill_signal_registry_safe() -> dict[str, Any]:
    try:
        from signal_registry import backfill_labels_from_oracle

        return await backfill_labels_from_oracle(limit=5000)
    except Exception:
        logger.exception("D8 signal registry backfill failed")
        return {"ok": False, "error": "d8_backfill_failed"}


async def run_labeling_flywheel_cycle(
    *,
    bootstrap_if_needed: bool = True,
    collect_live: bool = True,
) -> dict[str, Any]:
    from ml.experience_log import append_experience

    collect_stats = await _collect_live_samples_if_enabled(collect_live)
    bootstrap_stats = await _bootstrap_market_replay_if_needed(bootstrap_if_needed)
    resolve_stats = await resolve_mature_predictions()
    export_stats = await export_labeled_dataset()
    drift_stats = await _drift_monitoring_stats(export_stats, bootstrap_stats)
    train_stats = await _train_direction_model_if_enabled(export_stats)
    regime_train = await _train_regime_models_safe()
    d8_backfill = await _backfill_signal_registry_safe()
    payload = {
        "collect": collect_stats,
        "bootstrap": bootstrap_stats,
        "labeling": resolve_stats,
        "export": export_stats,
        "drift": drift_stats,
        "training": train_stats,
        "regime_training": regime_train,
        "signal_registry_backfill": d8_backfill,
        "timestamp": _utcnow_iso(),
    }
    append_experience("flywheel_cycle", payload)
    return payload
