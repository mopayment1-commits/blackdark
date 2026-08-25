"""
Decision Intelligence Engine (#48) — Core Product.

Gradual pipeline: prototype → backtest → paper trading → live signals.

Orchestrates:
  1. Data gathering (price, on-chain, funding, social, historical)
  2. 100+ feature extraction
  3. ML model inference + unified oracle + alpha engine
  4. Walk-forward backtest validation
  5. Explainable signal output with risk-adjusted performance
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.DecisionIntelligence")

_PIPELINE_STAGES = ("prototype", "backtest", "paper_trading", "live_candidate", "live")
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL = 120.0


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _build_reasoning(
    *,
    verdict: str,
    score: float,
    ml: dict[str, Any],
    alpha: dict[str, Any],
    features: dict[str, Any],
    top_factors: list[str],
) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []
    feat = features.get("features") or {}

    if ml.get("available"):
        reasons.append(
            {
                "factor": "ml_model",
                "direction": str(ml.get("prediction") or "neutral"),
                "weight": "high",
                "detail": f"ML confidence {ml.get('confidence', 0):.0f}% ({ml.get('engine', 'model')})",
            }
        )
    else:
        reasons.append(
            {
                "factor": "ml_model",
                "direction": "rules_fallback",
                "weight": "medium",
                "detail": f"ML unavailable: {ml.get('reason', 'not_trained')}",
            }
        )

    if alpha.get("ok"):
        reasons.append(
            {
                "factor": "alpha_engine",
                "direction": alpha.get("bias", "neutral"),
                "weight": "high",
                "detail": alpha.get("headline", "Alpha composite"),
            }
        )

    for factor in top_factors[:5]:
        val = feat.get(factor)
        if val is not None:
            reasons.append(
                {
                    "factor": factor,
                    "direction": "bullish" if float(val) > 0 else "bearish",
                    "weight": "medium",
                    "detail": f"{factor}={val}",
                }
            )

    reasons.append(
        {
            "factor": "unified_oracle",
            "direction": verdict.lower(),
            "weight": "high",
            "detail": f"Composite score {score:.0f}/100 → {verdict}",
        }
    )
    return reasons


async def generate_decision_signal(
    asset: str = "BTC",
    *,
    include_backtest: bool = True,
    price: float | None = None,
    change_24h: float = 0.0,
    quote_volume: float = 0.0,
) -> dict[str, Any]:
    """
    Decision Intelligence Engine — primary entrypoint.
    Produces actionable signal with confidence, reasoning, and risk metrics.
    """
    t0 = time.perf_counter()
    sym = asset.upper().replace("USDT", "")
    cache_key = f"{sym}:{include_backtest}"
    cached = _CACHE.get(cache_key)
    if cached and time.time() - cached[0] < _CACHE_TTL:
        out = dict(cached[1])
        out["cache_hit"] = True
        return out

    # 1. Feature extraction (100+)
    from ml.decision_features import extract_decision_features

    feature_pack = await extract_decision_features(sym, price_at=price)
    feature_count = feature_pack.get("feature_count", 0)

    # 2. ML inference
    from ml.inference import predict_direction

    ml = await predict_direction(sym, price=price, change_24h=change_24h)

    # 3. Alpha engine
    from bd_platform.alpha_engine import compute_alpha_signal

    alpha = await compute_alpha_signal(sym)

    # 4. Unified oracle
    from oracle_unified import compute_unified_oracle

    if not price:
        price = float((feature_pack.get("features") or {}).get("price") or 0)
    unified = await compute_unified_oracle(sym, price, quote_volume, change_24h)
    score = float(unified.get("score") or unified.get("opportunity_score") or 50)
    verdict = str(unified.get("verdict") or "WAIT")

    # 4b. Signal validation layer (#747 MTF convergence — filter, not standalone)
    from bd_platform.signal_validation_engine import run_signal_validation

    validation = await run_signal_validation(sym, opportunity_score=score)
    if not validation.get("signal_trusted"):
        score = float(validation.get("adjusted_score") or score)
        if validation.get("mtf_validation", {}).get("mtf_regime") == "divergent":
            verdict = "WAIT" if verdict in ("BUY", "Buy Now") else verdict

    # 5. Walk-forward backtest (optional, cached longer)
    backtest: dict[str, Any] = {"ok": False, "skipped": True}
    if include_backtest:
        try:
            from ml.walk_forward import run_walk_forward_backtest

            backtest = await run_walk_forward_backtest(sym, limit=2000)
        except Exception:
            logger.debug("walk-forward backtest failed", exc_info=True)
            backtest = {"ok": False, "error": "backtest_failed"}

    pipeline_stage = backtest.get("pipeline_stage", "prototype") if backtest.get("ok") else "prototype"
    metrics = (backtest.get("metrics") or {}) if backtest.get("ok") else {}

    # Confidence: blend ML + oracle + alpha
    ml_conf = float(ml.get("confidence") or 0) if ml.get("available") else 40.0
    alpha_conf = float(alpha.get("alpha_score") or 50) if alpha.get("ok") else 50.0
    oracle_conf = score
    confidence = round((ml_conf * 0.4 + oracle_conf * 0.35 + alpha_conf * 0.25), 1)

    # Top contributing features by magnitude
    feats = feature_pack.get("features") or {}
    ranked = sorted(
        ((k, abs(float(v))) for k, v in feats.items() if isinstance(v, (int, float))),
        key=lambda x: x[1],
        reverse=True,
    )
    top_factors = [k for k, _ in ranked[:8]]

    reasoning = _build_reasoning(
        verdict=verdict,
        score=score,
        ml=ml,
        alpha=alpha,
        features=feature_pack,
        top_factors=top_factors,
    )

    signal_action = "ACT" if verdict in ("BUY", "Buy Now") and confidence >= 60 else "WAIT"
    if verdict in ("SELL", "Do Not Touch", "CAUTION"):
        signal_action = "AVOID" if confidence >= 55 else "WAIT"

    alerts: list[dict[str, Any]] = []
    if backtest.get("ok") and not backtest.get("acceptance_met"):
        alerts.append(
            {
                "level": "medium",
                "code": "ACCEPTANCE_PENDING",
                "message": f"Pipeline stage: {pipeline_stage} — institutional targets not yet met",
            }
        )
    if not ml.get("available"):
        alerts.append(
            {
                "level": "low",
                "code": "ML_FALLBACK",
                "message": "Using rules engine — train ML model for higher confidence",
            }
        )

    result = {
        "ok": True,
        "surface": "decision_intelligence_engine",
        "feature": "#48",
        "asset": sym,
        "signal": {
            "action": signal_action,
            "verdict": verdict,
            "confidence": confidence,
            "score": round(score, 1),
            "ml_prediction": ml.get("prediction"),
            "alpha_bias": alpha.get("bias"),
        },
        "reasoning": reasoning,
        "explainability": {
            "top_factors": top_factors,
            "reason_count": len(reasoning),
            "engine": "decision_intelligence_v1",
        },
        "features": {
            "count": feature_count,
            "meets_100_plus": feature_pack.get("meets_100_plus", False),
            "sample": {k: feats[k] for k in top_factors[:5] if k in feats},
        },
        "ml": ml,
        "alpha": alpha if alpha.get("ok") else None,
        "unified_oracle": {
            "score": score,
            "verdict": verdict,
            "engine": unified.get("engine_id", "unified_multimodal_v1"),
        },
        "signal_validation": validation,
        "backtest": backtest,
        "risk_adjusted": {
            "sharpe": metrics.get("sharpe"),
            "max_drawdown_pct": metrics.get("max_drawdown_pct"),
            "win_rate": metrics.get("win_rate"),
            "total_return_pct": metrics.get("total_return_pct"),
            "acceptance_met": backtest.get("acceptance_met", False),
            "acceptance_criteria": backtest.get("acceptance_criteria"),
        },
        "pipeline": {
            "stage": pipeline_stage,
            "stages": list(_PIPELINE_STAGES),
            "next": "paper_trading" if pipeline_stage == "backtest" else "backtest",
        },
        "alerts": alerts,
        "headline": f"{sym} {signal_action} — {verdict} ({confidence:.0f}% confidence)",
        "data_sources": ["price", "onchain", "funding", "social", "historical", "ml", "alpha"],
        "data_state": "LIVE",
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "sla_met": (time.perf_counter() - t0) <= 300_000,  # ≤5 min acceptance
        "timestamp": _utcnow(),
        "disclaimer": "Decision intelligence — not financial advice. Gradual pipeline to institutional targets.",
    }

    _CACHE[cache_key] = (time.time(), result)
    return result


async def decision_intelligence_ranking(
    assets: list[str] | None = None,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    """Rank universe by decision intelligence confidence."""
    t0 = time.perf_counter()
    universe = assets or ["BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "AVAX", "LINK"]
    rankings: list[dict[str, Any]] = []
    for sym in universe[:limit]:
        try:
            sig = await generate_decision_signal(sym, include_backtest=False)
            rankings.append(
                {
                    "asset": sym,
                    "action": sig["signal"]["action"],
                    "confidence": sig["signal"]["confidence"],
                    "score": sig["signal"]["score"],
                    "verdict": sig["signal"]["verdict"],
                }
            )
        except Exception:
            logger.debug("ranking skip %s", sym, exc_info=True)
    rankings.sort(key=lambda r: r["confidence"], reverse=True)
    return {
        "ok": True,
        "surface": "decision_intelligence_ranking",
        "rankings": rankings,
        "count": len(rankings),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
        "timestamp": _utcnow(),
    }
