"""Oracle + ML flywheel API router."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends

from market_context import fetch_binance_ticker, normalize_oracle_symbol
from security_auth import require_admin

router = APIRouter(tags=["oracle"])


@router.get("/api/oracle/data-hub")
async def oracle_data_hub_overview():
    from oracle_data_hub import build_hub_context_safe

    return await build_hub_context_safe("BTC")


@router.get("/api/oracle/data-hub/{symbol}")
async def oracle_data_hub_asset(symbol: str):
    from oracle_data_hub import build_hub_context_safe, hub_score_adjustment

    asset = symbol.upper().replace("USDT", "").replace("/", "")
    ctx = await build_hub_context_safe(asset)
    delta, reasons, risks = hub_score_adjustment(asset, ctx)
    ctx["score_adjustment"] = delta
    ctx["hub_reasons"] = reasons
    ctx["hub_risks"] = risks
    return ctx


@router.get("/api/forecast/audit")
async def forecast_audit():
    from database import fetch_forecast_audit_stats
    from forecast_engine import run_forecast_audit

    audit_run = await run_forecast_audit()
    stats = await fetch_forecast_audit_stats(limit=25)
    stats["newly_resolved"] = audit_run.get("resolved", 0)
    stats["checked"] = audit_run.get("checked", 0)
    return stats


@router.get("/api/forecast/{symbol}")
async def forecast_asset(symbol: str):
    from forecast_engine import build_asset_forecast

    asset, pair = normalize_oracle_symbol(symbol)
    market = await fetch_binance_ticker(pair)
    current_price = float(market["price"]) if market else None
    forecast = await build_asset_forecast(asset, current_price=current_price)
    return {
        "asset": asset,
        "forecast": forecast,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/api/oracle/audit")
async def oracle_audit():
    from database import fetch_oracle_audit_stats
    from ml.labeling_pipeline import resolve_mature_predictions

    resolved_now = await resolve_mature_predictions()
    stats = await fetch_oracle_audit_stats(limit=25)
    stats["newly_resolved"] = (resolved_now or {}).get("resolved_24h", 0)
    stats["labeling"] = resolved_now
    return stats


@router.get("/api/ml/status")
async def ml_status():
    from ml.train_baseline import model_status

    return await model_status()


@router.post("/api/ml/flywheel/run")
async def ml_flywheel_run(_admin: dict = Depends(require_admin)):
    from ml.labeling_pipeline import run_labeling_flywheel_cycle

    return await run_labeling_flywheel_cycle(bootstrap_if_needed=True, collect_live=True)


@router.post("/api/ml/collect-live")
async def ml_collect_live(_admin: dict = Depends(require_admin)):
    from ml.live_sample_collector import collect_live_unified_samples

    return await collect_live_unified_samples()


@router.post("/api/ml/bootstrap-replay")
async def ml_bootstrap_replay(_admin: dict = Depends(require_admin)):
    from ml.market_replay_bootstrap import bootstrap_market_replay_dataset

    return await bootstrap_market_replay_dataset()


@router.post("/api/ml/train")
async def ml_train(_admin: dict = Depends(require_admin)):
    from ml.train_baseline import train_oracle_direction_model

    return await train_oracle_direction_model()


@router.get("/api/ml/predict/{asset}")
async def ml_predict(asset: str, price: float | None = None):
    from ml.inference import predict_direction

    return await predict_direction(asset, price=price)


@router.get("/api/oracle/accuracy/public")
async def oracle_accuracy_public():
    from ml.public_accuracy import build_public_accuracy_payload

    payload = await build_public_accuracy_payload()
    payload["timestamp"] = datetime.now(UTC).isoformat()
    return payload


@router.post("/api/ml/train/ensemble")
async def ml_train_ensemble(_admin: dict = Depends(require_admin)):
    from ml.train_ensemble import train_direction_ensemble

    return await train_direction_ensemble()


@router.get("/api/ml/experience")
async def ml_experience():
    from ml.experience_log import fetch_recent_experiences, load_experience_summary

    return {
        "summary": load_experience_summary(),
        "recent": fetch_recent_experiences(limit=50),
    }


@router.get("/api/oracle/weights")
async def oracle_weights(
    symbol: str = "BTC",
    change_24h: float = 0.0,
    _admin: dict = Depends(require_admin),
):
    from model_weights_guard import public_weights_summary
    from weight_aggregator import (
        compute_modal_breakdown,
        detect_market_regime,
        get_core_score_weights,
        get_dimension_weights,
        get_regime_dimension_weights,
    )
    from whale_tracker import get_latest_institutional_context

    ctx = await get_latest_institutional_context()
    regime = detect_market_regime(ctx, change_24h=change_24h)
    breakdown = compute_modal_breakdown(symbol.upper(), ctx, change_24h=change_24h)
    return {
        "symbol": symbol.upper(),
        "public_summary": public_weights_summary(regime),
        "market_regime": regime,
        "dimension_weights": get_regime_dimension_weights(regime),
        "stored_weights": get_dimension_weights(),
        "core_weights": get_core_score_weights(),
        "breakdown": breakdown,
        "engine": "unified_multimodal_v1",
        "access": "admin",
    }


@router.get("/api/oracle/weights/public")
async def oracle_weights_public(symbol: str = "BTC", change_24h: float = 0.0):
    from model_weights_guard import public_weights_summary
    from weight_aggregator import detect_market_regime
    from whale_tracker import get_latest_institutional_context

    ctx = await get_latest_institutional_context()
    regime = detect_market_regime(ctx, change_24h=change_24h)
    return public_weights_summary(regime)


@router.post("/api/oracle/retrain")
async def oracle_retrain_manual(_admin: dict = Depends(require_admin)):
    from oracle_retrainer import run_oracle_retrain_step

    return await run_oracle_retrain_step()


@router.get("/api/oracle/dimension-conflict")
async def api_dimension_conflict_guard():
    from dimension_conflict_guard import dimension_conflict_status

    return dimension_conflict_status()


@router.get("/api/oracle/track-record")
async def api_oracle_track_record():
    from oracle_track_record import public_track_record

    return public_track_record()


@router.post("/api/oracle/track-record/backfill")
async def api_oracle_track_record_backfill(_admin: dict = Depends(require_admin)):
    from oracle_track_record import backfill_from_database

    return await backfill_from_database()


@router.get("/api/oracle/audit-chain")
async def api_oracle_audit_chain(limit: int = 20):
    from oracle_audit_chain import chain_summary

    return chain_summary(limit=limit)


@router.get("/api/oracle/audit-chain/verify")
async def api_oracle_audit_chain_verify():
    from oracle_audit_chain import verify_chain

    return verify_chain()


@router.get("/api/oracle/net-edge-truth")
async def api_net_edge_truth_status():
    from net_edge_truth import net_edge_truth_status

    return net_edge_truth_status()


@router.get("/api/oracle/half-life")
async def api_opportunity_half_life():
    from opportunity_tracker import half_life_status

    return half_life_status()


@router.get("/api/oracle/signals")
async def api_signal_registry(
    limit: int = 50,
    signal_type: str | None = None,
    asset: str | None = None,
):
    from signal_registry import list_signals, registry_stats

    return {
        "stats": registry_stats(),
        "signals": list_signals(limit=limit, signal_type=signal_type, asset=asset),
    }


@router.get("/api/oracle/signals/summary")
async def api_signal_registry_summary():
    """Public D8 moat summary without full signal rows."""
    from signal_registry import registry_stats

    stats = registry_stats()
    return {
        "differentiator": "D8",
        "status": stats.get("status"),
        "total": stats.get("total_in_memory", 0),
        "labeled": stats.get("labeled", 0),
        "unlabeled": stats.get("unlabeled", 0),
        "linked_prediction_ids": stats.get("linked_prediction_ids", 0),
        "by_type": stats.get("by_type") or {},
        "by_label": stats.get("by_label") or {},
        "by_type_performance": stats.get("by_type_performance") or {},
        "lexicon": stats.get("lexicon") or {},
        "moat_claim": stats.get("moat_claim"),
        "generated_at": stats.get("generated_at"),
    }


@router.post("/api/oracle/signals/backfill")
async def api_signal_registry_backfill(_admin: dict = Depends(require_admin)):
    """Admin: label D8 registry rows from resolved oracle predictions."""
    from signal_registry import backfill_labels_from_oracle

    return await backfill_labels_from_oracle(limit=5000)


@router.get("/api/oracle/persona-clarity/demo")
async def api_persona_clarity_demo(
    asset: str = "BTC",
    score: float = 72.0,
    verdict: str = "Buy Now",
    net_profit_usdt: float = 0.42,
):
    from persona_clarity import build_persona_clarity

    return build_persona_clarity(
        asset=asset.upper(),
        score=score,
        verdict=verdict,
        payload={
            "market_regime": "risk_on",
            "net_edge_truth": {"truth_score": 78, "reject": False},
            "opportunity_half_life": {
                "expected_half_life_seconds": 16,
                "remaining_seconds": 9,
                "disappearance_probability": 0.41,
            },
        },
        net_profit_usdt=net_profit_usdt,
    )
