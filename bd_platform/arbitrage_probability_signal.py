"""
Arbitrage Probability Signal — Feature #422 (Intelligence Ledger / Arbitrage Scanner).

Early probability detection for forming arbitrage opportunities — NOT standalone.
Renamed from "Predictive Arbitrage" — no "5 seconds" or "Predictive" in product naming.

Rule-based v1 (no ML):
  - Order book imbalance
  - Funding rate differential
  - Volume spike
  - Correlation break

Integrations:
  - #403/#429 Arbitrage Scanner filter
  - #417 Net-Edge Truth projected net edge if opportunity forms
  - #415 Fill Feasibility for projected opportunity
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ArbitrageProbabilitySignal")

_FEATURE_ID = 422
_TITLE = "Arbitrage Probability Signal"
_LEGAL_NAME = "Arbitrage Probability Signal"
_RENAMED_FROM = "Predictive Arbitrage / Early probability detection"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Arbitrage Scanner (#403)"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/arbitrage_probability_signal_seed.json")
_METHODOLOGY_VERSION = "1.0"
_RULE_ENGINE_VERSION = "1.0.0"

_BANNED_TERMS = ("predictive arbitrage", "5 seconds", "5 second", "guaranteed")

_DISCLAIMER = (
    "Arbitrage Probability Signal — rule-based early detection of forming opportunities. "
    "Probability score with confidence level and expected formation time range (not fixed seconds). "
    "Near real-time analytics only — simulation, no automatic execution."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"market_signals": {}, "component_weights": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("arbitrage probability signal seed load failed: %s", exc)
        return {"market_signals": {}, "component_weights": {}}


def _confidence_level(score: float, seed: dict[str, Any]) -> str:
    thresholds = seed.get("confidence_thresholds") or {}
    if score >= float(thresholds.get("high", 75)):
        return "high"
    if score >= float(thresholds.get("medium", 50)):
        return "medium"
    if score >= float(thresholds.get("low", 25)):
        return "low"
    return "very_low"


def _formation_time_range(probability_pct: float, seed: dict[str, Any]) -> dict[str, Any]:
    ranges = seed.get("formation_time_ranges_sec") or {}
    if probability_pct >= 75:
        key = "high_probability"
    elif probability_pct >= 50:
        key = "medium_probability"
    else:
        key = "low_probability"
    bounds = ranges.get(key) or [30, 300]
    return {
        "range_sec": bounds,
        "label": f"{bounds[0]}–{bounds[1]} seconds (range, not guarantee)",
        "not_fixed_seconds": True,
    }


def _component_scores(signals: dict[str, Any], *, seed: dict[str, Any]) -> dict[str, Any]:
    weights = seed.get("component_weights") or {}
    imb = float(signals.get("order_book_imbalance", 0))
    imb_score = min(100.0, abs(imb - 0.5) * 200)

    fund_bps = abs(float(signals.get("funding_rate_differential_bps", 0)))
    fund_score = min(100.0, fund_bps * 8)

    vol_z = float(signals.get("volume_spike_zscore", 0))
    vol_score = min(100.0, max(0.0, (vol_z - 1.0) * 35))

    corr_break = bool(signals.get("correlation_break"))
    corr_score = 85.0 if corr_break else 20.0

    return {
        "order_book_imbalance": {
            "raw": imb,
            "score": round(imb_score, 2),
            "weight": weights.get("order_book_imbalance", 0.30),
        },
        "funding_rate_differential": {
            "raw_bps": fund_bps,
            "score": round(fund_score, 2),
            "weight": weights.get("funding_rate_differential", 0.25),
        },
        "volume_spike": {
            "zscore": vol_z,
            "score": round(vol_score, 2),
            "weight": weights.get("volume_spike", 0.25),
        },
        "correlation_break": {
            "detected": corr_break,
            "score": round(corr_score, 2),
            "weight": weights.get("correlation_break", 0.20),
        },
    }


def compute_probability_signal(
    asset: str,
    *,
    signals: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based probability score for forming arbitrage opportunity."""
    seed = seed or _load_seed()
    asset_u = asset.upper().split("/")[0]
    sig = signals or (seed.get("market_signals") or {}).get(asset_u) or {}

    components = _component_scores(sig, seed=seed)
    probability_pct = round(
        sum(c["score"] * c["weight"] for c in components.values()),
        2,
    )
    confidence = _confidence_level(probability_pct, seed)
    formation = _formation_time_range(probability_pct, seed)

    risk_warnings: list[str] = []
    if probability_pct < 50:
        risk_warnings.append("low_probability_forming")
    if sig.get("correlation_break"):
        risk_warnings.append("correlation_regime_break")
    if abs(float(sig.get("funding_rate_differential_bps", 0))) > 10:
        risk_warnings.append("extreme_funding_divergence")

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ref": _FEATURE_ID,
        "asset": asset_u,
        "probability_score_pct": probability_pct,
        "confidence_level": confidence,
        "expected_formation_time": formation,
        "risk_warnings": risk_warnings,
        "component_breakdown": components,
        "rule_engine_version": _RULE_ENGINE_VERSION,
        "ml_disabled_v1": seed.get("ml_disabled_v1", True),
        "inputs": sig,
        "near_real_time": True,
        "simulation_only": True,
        "timestamp": _utcnow(),
    }


def _projected_opportunity(sig: dict[str, Any], asset: str) -> dict[str, Any]:
    spread_bps = abs(float(sig.get("funding_rate_differential_bps", 0))) + 3.0
    return {
        "opportunity_type": "early_probability_projected",
        "asset": asset,
        "symbol": f"{asset}/USDT",
        "buy_venue": sig.get("buy_venue", "okx"),
        "sell_venue": sig.get("sell_venue", "binance"),
        "quote_usd": float(sig.get("quote_usd", 1000)),
        "gross_spread_bps": spread_bps,
        "quote_age_ms": 200,
    }


def enrich_with_integrations(
    probability: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach #417 projected net edge and #415 fill feasibility."""
    seed = seed or _load_seed()
    asset = probability.get("asset", "BTC")
    sig = (seed.get("market_signals") or {}).get(asset) or {}
    projected = _projected_opportunity(sig, asset)

    net_edge_projection = None
    fill_feasibility = None
    try:
        from bd_platform.unified_arbitrage_engine import compute_arbitrage_economics
        from fee_matrix import taker_fee, withdrawal_fee_usdt

        venue = str(projected.get("buy_venue") or "binance")
        fee_bps = (taker_fee(venue) or 0.001) * 10_000
        wd = withdrawal_fee_usdt(venue, asset) or 0.0
        econ = compute_arbitrage_economics(
            gross_spread_bps=float(projected["gross_spread_bps"]),
            quote_usd=float(projected["quote_usd"]),
            trading_fee_bps=fee_bps,
            slippage_bps=8.0,
            withdrawal_fee_usdt=wd,
        )
        projected_opp = {
            **projected,
            "net_edge_usdt": econ["net_edge_usdt"],
            "slippage_bps": 8.0,
            "trading_fees_usdt": econ["trading_fees_usdt"],
            "withdrawal_fee_usdt": wd,
        }
        from bd_platform.net_edge_truth_layer import evaluate_arbitrage_opportunity

        truth = evaluate_arbitrage_opportunity(projected_opp, enrich_feasibility=True)
        net_edge_projection = {
            "feature_ref": 417,
            "projected_net_edge_usdt": econ["net_edge_usdt"],
            "net_edge_truth": truth.get("net_edge_truth"),
            "rejection_reasons": truth.get("rejection_reasons"),
        }
        fill_feasibility = (truth.get("net_edge_truth") or {}).get("feasibility")
    except Exception:
        logger.debug("probability integration skipped", exc_info=True)

    return {
        **probability,
        "projected_opportunity": projected,
        "net_edge_projection_417": net_edge_projection,
        "fill_feasibility_415": fill_feasibility,
    }


def scan_probability_signals(
    assets: list[str] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    seed = seed or _load_seed()
    market = seed.get("market_signals") or {}
    targets = assets or list(market.keys())
    results = []
    for asset in targets:
        prob = compute_probability_signal(asset, seed=seed)
        results.append(enrich_with_integrations(prob, seed=seed))
    results.sort(key=lambda r: float(r.get("probability_score_pct", 0)), reverse=True)
    return results


def build_probability_backtest(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Probability Backtest — historical accuracy for trust building."""
    seed = seed or _load_seed()
    bt = seed.get("probability_backtest") or {}
    samples = seed.get("probability_history_samples") or []
    fpr = float(bt.get("false_positive_rate", 0))
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "backtest_period_days": bt.get("period_days", 30),
        "total_signals": bt.get("total_signals"),
        "validated_signals": bt.get("validated_signals"),
        "correct_predictions": bt.get("correct_predictions"),
        "false_positives": bt.get("false_positives"),
        "false_positive_rate": fpr,
        "accuracy_rate": bt.get("accuracy_rate"),
        "fpr_target": seed.get("acceptance", {}).get("false_positive_rate_max_backtest", 0.30),
        "meets_fpr_target": fpr <= float(seed.get("acceptance", {}).get("false_positive_rate_max_backtest", 0.30)),
        "cancelled_sla": seed.get("cancelled_sla"),
        "history_samples": samples,
        "trust_calibration": (
            "Shows historical false positive rate and accuracy — builds confidence "
            "without claiming fixed-second prediction or 95% accuracy SLA."
        ),
        "timestamp": _utcnow(),
    }


def build_probability_panel(
    asset: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    if asset:
        signals = [enrich_with_integrations(compute_probability_signal(asset, seed=seed), seed=seed)]
    else:
        signals = scan_probability_signals(seed=seed)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "signals": signals,
        "count": len(signals),
        "backtest": build_probability_backtest(seed=seed),
        "rule_engine_version": _RULE_ENGINE_VERSION,
        "ml_disabled_v1": True,
        "near_real_time": True,
        "disclaimer": _DISCLAIMER,
        "simulation_only": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def arbitrage_probability_signal_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "rule_engine_version": _RULE_ENGINE_VERSION,
        "ml_disabled_v1": seed.get("ml_disabled_v1", True),
        "components": list((seed.get("component_weights") or {}).keys()),
        "acceptance": seed.get("acceptance"),
        "cancelled_sla": seed.get("cancelled_sla"),
        "integrations": seed.get("integrations") or {},
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "403 filter"})
    checks.append({"id": "renamed_no_predictive", "passed": "Predictive" not in seed.get("legal_name", ""), "detail": seed.get("legal_name")})
    checks.append({"id": "ml_disabled_v1", "passed": seed.get("ml_disabled_v1") is True, "detail": "rule-based"})
    checks.append({"id": "fpr_target", "passed": (seed.get("probability_backtest") or {}).get("meets_fpr_target") is True, "detail": "FPR≤30%"})

    sig = compute_probability_signal("BTC", seed=seed)
    checks.append({"id": "probability_score_output", "passed": "probability_score_pct" in sig and "confidence_level" in sig, "detail": str(sig.get("probability_score_pct"))})
    checks.append({"id": "formation_time_range", "passed": sig.get("expected_formation_time", {}).get("not_fixed_seconds") is True, "detail": "no fixed 5s"})

    enriched = enrich_with_integrations(sig, seed=seed)
    checks.append({"id": "net_edge_417_integration", "passed": enriched.get("net_edge_projection_417") is not None, "detail": "417"})

    backtest = build_probability_backtest(seed=seed)
    checks.append({"id": "probability_backtest", "passed": backtest.get("meets_fpr_target") is True, "detail": f"fpr={backtest.get('false_positive_rate')}"})

    panel = build_probability_panel(seed=seed)
    checks.append({"id": "arbitrage_scanner_panel", "passed": panel.get("count", 0) >= 1, "detail": f"count={panel.get('count')}"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
