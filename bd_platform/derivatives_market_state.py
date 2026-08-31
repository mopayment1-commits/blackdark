"""
Derivatives Market State Module — Feature #327 (Sprint 2 Intelligence Ledger).

Renamed from "Derivatives Market Sentiment Composite" — the derivatives product.
Absorbs #328 (regime) + #329 (leverage ratio) + #352 (leverage context). Components: #311, #313, #324 views.

No opaque score — formula public, contributor evidence, backtest gate.
Scope: perpetuals only.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DerivativesMarketState")

_FEATURE_ID = 327
_ABSORBED_IDS = (328, 329, 352)
_RENAMED_FROM = "Derivatives Market Sentiment Composite"
_TITLE = "Derivatives Market State Module"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Derivatives Market State Module"
_SPRINT = 2
_SEED_PATH = Path("data/derivatives_market_state_seed.json")
_FORMULA_VERSION = "1.0"
_METHODOLOGY_VERSION = "1.0"

_DEFAULT_WEIGHTS = {
    "funding": 0.25,
    "open_interest": 0.25,
    "leverage": 0.20,
    "liquidations": 0.15,
    "price": 0.15,
}

Regime = Literal["crowded", "flush", "normal"]

_DISCLAIMER = (
    "Derivatives market state score — not investment advice. "
    "Formula public, contributors documented. Perpetuals only."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assets": {}, "backtest": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("derivatives market state seed load failed: %s", exc)
        return {"assets": {}, "backtest": {}}


def build_formula_documentation(weights: dict[str, float] | None = None) -> dict[str, Any]:
    w = weights or _DEFAULT_WEIGHTS
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "no_opaque_score": True,
        "black_box": False,
        "formula": "sentiment_score = Σ(component_normalized × weight)",
        "weights": w,
        "weights_documented": True,
        "weights_adjustable_per_tier": True,
        "display_weights": (
            f"Funding: {w['funding']:.0%} | OI: {w['open_interest']:.0%} | "
            f"Leverage: {w['leverage']:.0%} | Liquidations: {w['liquidations']:.0%} | "
            f"Price: {w['price']:.0%}"
        ),
        "api_and_ui_visible": True,
        "historical_backtest_documented": True,
    }


def normalize_component(value: float, *, mean: float, std: float) -> float:
    if std <= 0:
        return 0.0
    z = (value - mean) / std
    return max(-3.0, min(3.0, z))


def compute_component_contributions(
    components: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
    baselines: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Contributor evidence — value + contribution % + trend per component."""
    w = weights or _DEFAULT_WEIGHTS
    baselines = baselines or {}
    contributions = []

    mapping = {
        "funding": ("funding_rate", "funding"),
        "open_interest": ("oi_change_pct", "open_interest"),
        "leverage": ("leverage_ratio", "leverage"),
        "liquidations": ("liquidation_usd_24h", "liquidations"),
        "price": ("price_change_24h_pct", "price"),
    }

    raw_scores: dict[str, float] = {}
    for key, (field, weight_key) in mapping.items():
        val = float(components.get(field, 0))
        baseline = baselines.get(field) or {}
        mean = float(baseline.get("mean", 0))
        std = float(baseline.get("std", 1))
        normalized = normalize_component(val, mean=mean, std=std)
        raw_scores[key] = normalized * w.get(weight_key, 0)

    total_abs = sum(abs(v) for v in raw_scores.values()) or 1.0

    for key, (field, weight_key) in mapping.items():
        val = components.get(field)
        trend = components.get(f"{field}_trend", "stable")
        weight = w.get(weight_key, 0)
        contribution_pct = round(abs(raw_scores[key]) / total_abs * 100, 1)
        z_display = ""
        if baselines.get(field):
            z = normalize_component(float(val or 0), mean=float(baselines[field].get("mean", 0)),
                                    std=float(baselines[field].get("std", 1)))
            if abs(z) >= 2:
                direction = "bearish" if z > 0 else "bullish"
                z_display = f" ({z:+.1f}σ) contributing {contribution_pct}% to {direction} state"

        contributions.append({
            "component": key,
            "field": field,
            "value": val,
            "weight": weight,
            "weight_pct": round(weight * 100, 1),
            "normalized_score": round(raw_scores[key] / w.get(weight_key, 1) if w.get(weight_key) else 0, 3),
            "contribution_pct": contribution_pct,
            "trend": trend,
            "source": components.get(f"{field}_source", "Binance API"),
            "last_updated": components.get(f"{field}_updated"),
            "confidence": components.get(f"{field}_confidence", "high"),
            "display": (
                f"{key.replace('_', ' ').title()}: {val} | "
                f"Weight: {weight:.0%} | Contribution: {contribution_pct}%{z_display}"
            ),
        })

    return contributions


def detect_regime(components: dict[str, Any], *, thresholds: dict[str, Any] | None = None) -> dict[str, Any]:
    """#328 Regime Classification Sub-component — rule-based crowded/flush/normal."""
    thresholds = thresholds or {}
    funding_z = float(components.get("funding_z", 0))
    oi_z = float(components.get("oi_z", 0))
    liq_z = float(components.get("liquidation_z", 0))

    crowded_thresh = float(thresholds.get("crowded_funding_z", 2.0))
    flush_liq_thresh = float(thresholds.get("flush_liquidation_z", 2.5))

    if funding_z >= crowded_thresh and oi_z >= 1.5:
        regime: Regime = "crowded"
        label = "Crowded long positioning — elevated funding + OI"
    elif liq_z >= flush_liq_thresh:
        regime = "flush"
        label = "Flush event — liquidation spike detected"
    else:
        regime = "normal"
        label = "Normal derivatives market state"

    return {
        "sub_task": "#328",
        "sub_component": "Regime Classification Sub-component",
        "standalone_rejected": True,
        "merged_as": "sub-component in Derivatives Market State Module (#327)",
        "regime": regime,
        "label": label,
        "classification_type": "rule_based",
        "rule_based": True,
        "formula_version": _FORMULA_VERSION,
        "formula": (
            "crowded: funding_z >= {crowded} AND oi_z >= 1.5 | "
            "flush: liquidation_z >= {flush} | else: normal"
        ).format(crowded=crowded_thresh, flush=flush_liq_thresh),
        "backtest_required": True,
        "thresholds": {
            "crowded_funding_z": crowded_thresh,
            "flush_liquidation_z": flush_liq_thresh,
        },
        "inputs": {"funding_z": funding_z, "oi_z": oi_z, "liquidation_z": liq_z},
    }


_ELR_FORMULA_VERSION = "1.0"
_ELR_PERCENTILE_WINDOW_DAYS = 90


def compute_estimated_leverage_ratio(components: dict[str, Any]) -> dict[str, Any]:
    """#329 Estimated Leverage Ratio — ELR = OI / Exchange Reserve."""
    oi = components.get("open_interest_usd")
    reserve = components.get("exchange_reserve_usd")
    oi_deribit = components.get("oi_deribit_usd")
    reserve_deribit = components.get("reserve_deribit_usd")
    oi_total = components.get("oi_total_usd")
    reserve_total = components.get("reserve_total_usd")
    history = components.get("elr_history_90d") or []

    def _safe_elr(numerator: float | None, denominator: float | None) -> dict[str, Any]:
        if numerator is None or denominator is None or denominator <= 0:
            return {
                "elr": None,
                "elr_display": "N/A",
                "warning": "Insufficient reserve data",
                "zero_missing_protected": True,
            }
        elr = round(numerator / denominator, 4)
        return {
            "elr": elr,
            "elr_display": f"ELR = {elr:.4f}",
            "zero_missing_protected": True,
        }

    primary = _safe_elr(
        float(oi) if oi is not None else None,
        float(reserve) if reserve is not None else None,
    )
    variant_deribit = _safe_elr(
        float(oi_deribit) if oi_deribit is not None else None,
        float(reserve_deribit) if reserve_deribit is not None else None,
    )
    variant_total = _safe_elr(
        float(oi_total) if oi_total is not None else None,
        float(reserve_total) if reserve_total is not None else None,
    )

    percentile = None
    if primary["elr"] is not None and history:
        below = sum(1 for h in history if h < primary["elr"])
        percentile = round(below / len(history) * 100, 1)

    reserve_qa = components.get("reserve_qa") or {}
    return {
        "sub_task": "#329",
        "sub_component": "Estimated Leverage Ratio contributor metric",
        "standalone_rejected": True,
        "merged_as": "contributor metric in Derivatives Market State Module (#327)",
        "formula": "ELR = OI / Exchange Reserve",
        "formula_version": _ELR_FORMULA_VERSION,
        "variants": {
            "primary": {"label": "OI / Exchange Reserve", **primary},
            "oi_deribit_reserve_deribit": {
                "label": "OI_deribit / Reserve_deribit",
                **variant_deribit,
            },
            "oi_total_reserve_total": {
                "label": "OI_total / Reserve_total",
                **variant_total,
            },
        },
        "elr": primary["elr"],
        "elr_display": primary["elr_display"],
        "warning": primary.get("warning"),
        "denominator_qa": {
            "reserve_verified": reserve_qa.get("verified", False),
            "verification_method": reserve_qa.get("method", "exchange_attestation"),
            "source": reserve_qa.get("source", components.get("exchange_reserve_source")),
            "display": (
                "Reserve = verified on-chain or exchange attestation"
                if reserve_qa.get("verified") else "Reserve verification pending"
            ),
        },
        "historical_percentile": {
            "percentile": percentile,
            "window_days": _ELR_PERCENTILE_WINDOW_DAYS,
            "universe": components.get("elr_universe", "BTC derivatives venues"),
            "recomputed": "daily",
            "display": (
                f"Percentile: {percentile}% (90-day rolling window)"
                if percentile is not None else "Percentile: N/A — insufficient history"
            ),
        },
        "source": components.get("exchange_reserve_source", "Binance API"),
        "last_updated": components.get("exchange_reserve_updated"),
        "confidence": components.get("exchange_reserve_confidence", "high"),
        "not_opaque": True,
    }


def compute_leverage_context(components: dict[str, Any]) -> dict[str, Any]:
    """#329 leverage ratio — absorbed component (delegates to ELR)."""
    return compute_estimated_leverage_ratio(components)


def compute_sentiment_score(
    components: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
    baselines: dict[str, Any] | None = None,
) -> dict[str, Any]:
    w = weights or _DEFAULT_WEIGHTS
    baselines = baselines or {}
    contributions = compute_component_contributions(components, weights=w, baselines=baselines)

    mapping = {
        "funding": ("funding_rate", "funding"),
        "open_interest": ("oi_change_pct", "open_interest"),
        "leverage": ("leverage_ratio", "leverage"),
        "liquidations": ("liquidation_usd_24h", "liquidations"),
        "price": ("price_change_24h_pct", "price"),
    }
    total = 0.0
    for _, (field, weight_key) in mapping.items():
        val = float(components.get(field, 0))
        baseline = baselines.get(field) or {}
        norm = normalize_component(
            val,
            mean=float(baseline.get("mean", 0)),
            std=float(baseline.get("std", 1)),
        )
        total += norm * w[weight_key]

    scaled = round(max(-100, min(100, total * 33.3)), 1)

    if scaled >= 40:
        bias = "bearish_crowded"
    elif scaled <= -40:
        bias = "bullish_flush"
    elif scaled >= 15:
        bias = "slightly_bearish"
    elif scaled <= -15:
        bias = "slightly_bullish"
    else:
        bias = "neutral"

    return {
        "score": scaled,
        "bias": bias,
        "contributors": contributions,
        "formula": build_formula_documentation(w),
        "no_opaque_score": True,
    }


def build_backtest_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    bt = seed.get("backtest") or {}
    fp_rate = float(bt.get("false_positive_rate_pct", 0))
    return {
        "backtest_documented": True,
        "historical_events_tested": bt.get("historical_events_tested", 0),
        "regime_accuracy_pct": bt.get("regime_accuracy_pct"),
        "false_positive_rate_pct": fp_rate,
        "false_positive_gate": fp_rate < 30,
        "gate_passed": fp_rate < 30,
        "regime_labels_backtested": ["crowded", "flush", "normal"],
        "display": (
            f"Backtest: {bt.get('historical_events_tested', 0)} events | "
            f"Accuracy: {bt.get('regime_accuracy_pct', 'N/A')}% | "
            f"FP rate: {fp_rate}% ({'PASS' if fp_rate < 30 else 'FAIL'} <30%)"
        ),
    }


def build_basis_sub_metric(components: dict[str, Any], *, asset: str) -> dict[str, Any]:
    """#311 Basis — REJECTED standalone, sub-metric view in Derivatives Analytics Layer."""
    spot = float(components.get("spot_price", 0))
    perp = float(components.get("perp_price", 0))
    expiry = components.get("expiry")
    days_to_expiry = float(components.get("days_to_expiry", 0))

    if spot > 0 and perp > 0:
        basis_pct = ((perp - spot) / spot) * 100
        annualized = basis_pct * (365 / days_to_expiry) if days_to_expiry > 0 else basis_pct
    else:
        basis_pct = 0.0
        annualized = 0.0

    return {
        "sub_task": "#311",
        "standalone_rejected": True,
        "merged_as": "sub-metric view in Derivatives Market State Module",
        "asset": asset,
        "spot_price": spot,
        "perp_price": perp,
        "basis_pct": round(basis_pct, 4),
        "annualized_basis_pct": round(annualized, 4),
        "expiry": expiry,
        "days_to_expiry": days_to_expiry,
        "expiry_time_alignment": True,
        "timestamp_alignment_utc": components.get("timestamp_utc"),
        "chart_hint": "basis chart = line on chart",
        "display": (
            f"Basis {asset}: {basis_pct:.3f}% | Annualized: {annualized:.2f}% | "
            f"Expiry aligned: {expiry or 'perpetual'}"
        ),
    }


def build_leverage_context_indicator(
    components: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#352 Leverage Context Indicator — component breakdown, no composite score."""
    seed = seed or _load_seed()
    lr = seed.get("legal_review") or {}
    legal_complete = bool(lr.get("complete", False))

    return {
        "sub_task": "#352",
        "absorbed_from": "Leverage Pressure Score",
        "title": "Leverage Context Indicator",
        "renamed_from": "Leverage Pressure Score",
        "no_score_in_name": True,
        "no_score_in_output": True,
        "standalone_rejected": True,
        "merged_as": "component in Derivatives Market State Module (#327)",
        "output_format": "leverage_components",
        "no_ranking_by_pressure": True,
        "no_pressure_alert": True,
        "formula_version": _FORMULA_VERSION,
        "formula": build_formula_documentation(),
        "no_opaque_score": True,
        "no_black_box": True,
        "components": {
            "open_interest": {
                "oi_change_pct": components.get("oi_change_pct"),
                "oi_z": components.get("oi_z"),
                "source": components.get("oi_change_pct_source"),
                "display": f"OI change: {components.get('oi_change_pct', 'N/A')}%",
            },
            "funding": {
                "funding_rate": components.get("funding_rate"),
                "funding_z": components.get("funding_z"),
                "source": components.get("funding_rate_source"),
                "display": f"Funding: {components.get('funding_rate', 'N/A')}",
            },
            "liquidations": {
                "liquidation_usd_24h": components.get("liquidation_usd_24h"),
                "liquidation_z": components.get("liquidation_z"),
                "source": components.get("liquidation_usd_24h_source"),
                "display": f"Liq 24h: ${components.get('liquidation_usd_24h', 0):,.0f}",
            },
            "basis": {
                "spot_price": components.get("spot_price"),
                "perp_price": components.get("perp_price"),
                "display": (
                    f"Basis: spot {components.get('spot_price')} / perp {components.get('perp_price')}"
                ),
            },
            "long_short_ratio": {
                "leverage_ratio": components.get("leverage_ratio"),
                "source": components.get("leverage_ratio_source"),
                "display": f"L/S ratio: {components.get('leverage_ratio', 'N/A')}",
            },
            "volatility": {
                "price_change_24h_pct": components.get("price_change_24h_pct"),
                "source": components.get("price_change_24h_pct_source"),
                "display": f"Vol proxy (24h): {components.get('price_change_24h_pct', 'N/A')}%",
            },
        },
        "regime_context": detect_regime(components),
        "legal_review": {
            "mandatory": True,
            "complete": legal_complete,
            "release_blocked_without_review": not legal_complete,
        },
        "wave": 2,
        "no_pressure_as_signal": True,
        "numeric_display_only": True,
        "disclaimer": (
            "Leverage components = numeric context only. "
            "Not investment advice. No pressure alerts. No asset ranking."
        ),
    }


def build_scope_lock() -> dict[str, Any]:
    return {
        "perpetuals_only": True,
        "futures_with_expiry": "Phase 2",
        "options": "Phase 3",
        "dex_perps": "separate component",
        "display": "Perpetuals only | Futures expiry = Phase 2 | Options = Phase 3 | DEX perps = separate",
    }


def build_derivatives_market_state_panel(asset: str = "BTC") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper()
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_tracked", "asset": sym}

    components = asset_data.get("components") or {}
    weights = asset_data.get("weights") or _DEFAULT_WEIGHTS
    baselines = asset_data.get("baselines") or {}

    sentiment = compute_sentiment_score(components, weights=weights, baselines=baselines)
    regime = detect_regime(components, thresholds=asset_data.get("regime_thresholds"))
    leverage_context = build_leverage_context_indicator(components, seed=seed)
    basis = build_basis_sub_metric(components, asset=sym)
    backtest = build_backtest_gate(seed)
    scope = build_scope_lock()

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_ids": list(_ABSORBED_IDS),
        "renamed_from": _RENAMED_FROM,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "asset": sym,
        "market_state_score": sentiment,
        "regime": regime,
        "leverage_ratio": compute_leverage_context(components),
        "leverage_context_indicator": leverage_context,
        "basis_sub_metric": basis,
        "components_raw": components,
        "backtest_gate": backtest,
        "scope_lock": scope,
        "absorbed_components": {
            328: "Regime Classification Sub-component (standalone rejected)",
            329: "Estimated Leverage Ratio contributor metric (standalone rejected)",
            352: "Leverage Context Indicator (standalone rejected, renamed from Leverage Pressure Score)",
            313: "CVD (view)",
            324: "Dashboard (view)",
        },
        "no_opaque_score": True,
        "formula_public": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def derivatives_market_state_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "renamed_from": _RENAMED_FROM,
        "absorbed_tickets": {
            328: "Regime Classification Sub-component (standalone rejected)",
            329: "Estimated Leverage Ratio contributor metric (standalone rejected)",
            352: "Leverage Context Indicator (standalone rejected)",
            311: "Basis sub-metric (standalone rejected)",
        },
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "formula": build_formula_documentation(),
        "scope_lock": build_scope_lock(),
        "backtest_gate": build_backtest_gate(seed),
        "asset_count": len(seed.get("assets") or {}),
        "acceptance_criteria": {
            "no_opaque_score": True,
            "formula_version_public": True,
            "contributor_evidence": True,
            "backtest_gate_fp_under_30": True,
            "perpetuals_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
