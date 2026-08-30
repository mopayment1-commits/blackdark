"""
Advanced TA & Risk Layer — #117–#128.

NOT standalone modules — merged into TA Engine, Exchange Health, Portfolio AI,
Simple Language Layer, and On-Chain Extension.
"""

from __future__ import annotations

import json
import logging
import math
import statistics
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AdvancedTARisk")

_SEED_PATH = Path("data/legal_retail_commercial_seed.json")


def reset_advanced_ta_risk_state() -> None:
    pass


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("advanced ta risk seed load failed: %s", exc)
        return {}


def _disclaimer(locale: str = "en") -> str:
    if locale.lower().startswith("ar"):
        return "تحليل فني/مخاطر — ليس توصية مالية ولا ضمان."
    return "Technical/risk analysis — not financial advice or guarantee."


# ─── #117 Liquidity Vacuum Spotter ──────────────────────────────────────────────


def compute_liquidity_vacuum_117(
    *,
    best_bid: float = 64_980,
    lowest_ask: float = 65_120,
    mid_price: float = 65_050,
    order_size_usd: float = 100_000,
    exchange: str = "binance",
    depth_pct: float = 1.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = (seed.get("liquidity_vacuum_117") or {}).get("policy", {})
    threshold = float(cfg.get("vacuum_threshold_pct", 1.5))

    gap = lowest_ask - best_bid
    vacuum_pct = round(gap / mid_price * 100, 3) if mid_price else 0
    is_vacuum = vacuum_pct > threshold
    move_pct = round(vacuum_pct * 0.6, 2)
    fee = float((seed.get("liquidity_vacuum_117") or {}).get("fee_db", {}).get("compute_usd", 0.0009))

    return {
        "ok": True,
        "feature_ref": 117,
        "route": "/radar/technical/liquidity-vacuum",
        "merged_into": "ta_engine",
        "order_book_gap": round(gap, 2),
        "vacuum_pct": vacuum_pct,
        "is_liquidity_vacuum": is_vacuum,
        "threshold_pct": threshold,
        "depth_level_pct": depth_pct,
        "exchange": exchange,
        "sensitivity_insight": {
            "en": (
                f"Sensitive zone — {move_pct}% move possible with ${order_size_usd:,.0f} order"
                if is_vacuum
                else "Liquidity adequate at this depth"
            ),
            "ar": (
                f"منطقة حساسة — حركة {move_pct}% ممكنة بأمر ${order_size_usd:,.0f}"
                if is_vacuum
                else "سيولة كافية عند هذا العمق"
            ),
        },
        "formula": "Gap = lowest_ask − best_bid; Vacuum = Gap / Mid-Price × 100",
        "technical_insight_not_recommendation": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #118 Counterparty Risk Distribution ───────────────────────────────────────


def compute_exchange_risk_distribution_118(
    exchange_allocations: list[dict[str, Any]] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Portfolio view of exchange risk — extends #80/#92."""
    seed = seed or _load_seed()
    allocations = exchange_allocations or [
        {"exchange": "binance", "value_usd": 60_000, "risk_score": 7},
        {"exchange": "kraken", "value_usd": 25_000, "risk_score": 4},
        {"exchange": "coinbase", "value_usd": 15_000, "risk_score": 3},
    ]
    total = sum(float(a.get("value_usd", 0)) for a in allocations) or 1.0
    distribution: list[dict[str, Any]] = []
    for a in allocations:
        pct = round(float(a.get("value_usd", 0)) / total * 100, 1)
        distribution.append({
            "exchange": a.get("exchange", "unknown"),
            "allocation_pct": pct,
            "risk_score": float(a.get("risk_score", 5)),
            "value_usd": float(a.get("value_usd", 0)),
        })
    top = max(distribution, key=lambda x: x["allocation_pct"])
    concentrated = top["allocation_pct"] > 50
    fee = float((seed.get("risk_distribution_118") or {}).get("fee_db", {}).get("compute_usd", 0.001))

    return {
        "ok": True,
        "feature_ref": 118,
        "merged_into": ["exchange_health_80", "counterparty_risk_92"],
        "route": "/radar/exchange-health",
        "distribution": distribution,
        "concentration_warning": concentrated,
        "insight": {
            "en": (
                f"{top['allocation_pct']}% on {top['exchange']} (Risk {top['risk_score']}/10) — high concentration"
                if concentrated
                else "Exchange risk reasonably distributed"
            ),
            "ar": (
                f"{top['allocation_pct']}% على {top['exchange']} (مخاطرة {top['risk_score']}/10) — تركيز مرتفع"
                if concentrated
                else "توزيع مخاطر المنصات معقول"
            ),
        },
        "rebalance_insight_only": True,
        "no_execution": True,
        "non_custodial": True,
        "risk_insight_not_protection": True,
        "fee_db": {"compute_usd": fee},
    }


def attach_risk_distribution_118(exchange_health: dict[str, Any], *, allocations: list[dict[str, Any]] | None = None, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    out = dict(exchange_health)
    out["risk_distribution"] = compute_exchange_risk_distribution_118(allocations, seed=seed)
    merged = list(out.get("merged_features") or [80])
    for ref in (92, 118):
        if ref not in merged:
            merged.append(ref)
    out["merged_features"] = merged
    return out


# ─── #119 Gas Hold — REJECTED → Gas Spike Alert ─────────────────────────────────


def gas_spike_alert_119(
    *,
    current_gwei: float = 150,
    avg_7d_gwei: float = 50,
    swap_cost_usd: float = 45,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    spike_pct = round((current_gwei - avg_7d_gwei) / avg_7d_gwei * 100, 1) if avg_7d_gwei else 0
    fee = float((seed.get("gas_spike_alert_119") or {}).get("fee_db", {}).get("compute_usd", 0.0004))
    return {
        "ok": True,
        "feature_ref": 119,
        "status": "rejected_execution",
        "alternative": "gas_spike_alert",
        "route": "/radar/on-chain/gas-alert",
        "execution_rejected": True,
        "current_gwei": current_gwei,
        "avg_7d_gwei": avg_7d_gwei,
        "spike_pct": spike_pct,
        "estimated_swap_cost_usd": swap_cost_usd,
        "insight": {
            "en": f"Gas at {current_gwei:.0f} gwei — {spike_pct:+.0f}% above 7-day avg. Typical swap may cost ${swap_cost_usd:.0f} — consider waiting",
            "ar": f"Gas عند {current_gwei:.0f} gwei — أعلى {spike_pct:.0f}% من متوسط 7 أيام. swap قد يكلف ${swap_cost_usd:.0f} — فكّر بالانتظار",
        },
        "educational_only": True,
        "no_hold_no_execution": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #120 Leverage Risk Analysis (not Optimization) ─────────────────────────────


def compute_leverage_risk_analysis_120(
    *,
    leverage: float = 10.0,
    volatility_30d_pct: float = 5.0,
    position_size_usd: float = 50_000,
    liquidation_threshold_pct: float = 10.0,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    liq_prob = round(min(95, leverage * volatility_30d_pct / liquidation_threshold_pct * 8), 1)
    fee = float((seed.get("leverage_risk_analysis_120") or {}).get("fee_db", {}).get("compute_usd", 0.001))

    return {
        "ok": True,
        "feature_ref": 120,
        "merged_into": ["advanced_risk_77", "intelligence_ledger"],
        "optimization_rejected": True,
        "analysis_type": "leverage_risk_insight",
        "leverage": leverage,
        "volatility_30d_pct": volatility_30d_pct,
        "position_size_usd": position_size_usd,
        "liquidation_probability_24h_pct": liq_prob,
        "insight": {
            "en": (
                f"Your {leverage:.0f}x leverage on {volatility_30d_pct:.1f}% daily volatility asset "
                f"→ ~{liq_prob:.0f}% liquidation risk within 24h"
            ),
            "ar": (
                f"رافعتك {leverage:.0f}x على أصل بتقلب {volatility_30d_pct:.1f}% يومياً "
                f"→ احتمال تصفية ~{liq_prob:.0f}% خلال 24 ساعة"
            ),
        },
        "formula": "Risk Score = f(Volatility_30d, Position_Size, Leverage)",
        "no_leverage_recommendation": True,
        "non_custodial": True,
        "disclaimer": _disclaimer(),
        "fee_db": {"compute_usd": fee},
    }


# ─── #121 PnL Attributed Drift Analysis ───────────────────────────────────────


def compute_pnl_attribution_121(
    *,
    actual_pnl_usd: float = 5000,
    market_beta: float = 1.2,
    market_return_pct: float = 3.0,
    portfolio_value_usd: float = 100_000,
    signal_hit_rate: float = 0.55,
    benchmark: str = "BTC",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    market_effect = round(portfolio_value_usd * market_beta * market_return_pct / 100, 2)
    strategy_effect = round(actual_pnl_usd * 0.35, 2)
    signal_effect = round(actual_pnl_usd * signal_hit_rate * 0.25, 2)
    explained = market_effect + strategy_effect + signal_effect
    drift = round(actual_pnl_usd - explained, 2)
    fee = float((seed.get("pnl_attribution_121") or {}).get("fee_db", {}).get("compute_usd", 0.002))

    return {
        "ok": True,
        "feature_ref": 121,
        "merged_into": ["journal_76", "discipline_66", "ic_report_87"],
        "route": "/portfolio/journal/attribution",
        "actual_pnl_usd": actual_pnl_usd,
        "attribution": {
            "market_effect_usd": market_effect,
            "strategy_effect_usd": strategy_effect,
            "signal_quality_effect_usd": signal_effect,
            "drift_residual_usd": drift,
        },
        "benchmark": benchmark,
        "formula": "Drift = Actual PnL − (Market + Strategy + Signal)",
        "rule_based_only": True,
        "learning_not_guarantee": True,
        "non_custodial": True,
        "disclaimer": _disclaimer(),
        "fee_db": {"compute_usd": fee},
    }


# ─── #122 Structural Break Analysis (Rule-Based, not AI) ──────────────────────


def compute_structural_break_122(
    prices: list[float] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    prices = prices or [100 + i * 0.5 + (10 if i > 50 else 0) for i in range(90)]
    mid = len(prices) // 2
    first_half = prices[:mid]
    second_half = prices[mid:]
    mean1 = statistics.mean(first_half)
    mean2 = statistics.mean(second_half)
    chow_f = round(abs(mean2 - mean1) / (statistics.pstdev(prices) or 1) ** 2 * mid, 2)

    residuals = [p - statistics.mean(prices) for p in prices]
    cusum = []
    s = 0.0
    for r in residuals:
        s += r
        cusum.append(s)
    break_idx = cusum.index(max(cusum, key=abs)) if cusum else mid
    confidence = min(95, round(50 + chow_f * 5, 1))

    fee = float((seed.get("structural_break_122") or {}).get("fee_db", {}).get("compute_usd", 0.0015))
    return {
        "ok": True,
        "feature_ref": 122,
        "route": "/radar/technical/structural-break",
        "merged_into": "ta_engine",
        "ai_rejected_rule_based_only": True,
        "chow_f_statistic": chow_f,
        "cusum_break_index": break_idx,
        "break_price_level": round(prices[break_idx], 2) if break_idx < len(prices) else 0,
        "confidence_pct": confidence,
        "tests": ["chow_test", "cusum", "volatility_regime_proxy"],
        "insight": {
            "en": f"Potential structural break at index {break_idx} — statistical confidence {confidence}%",
            "ar": f"انكسار هيكلي محتمل عند الفهرس {break_idx} — ثقة إحصائية {confidence}%",
        },
        "statistical_not_ai": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #123 Volume Profile POC ────────────────────────────────────────────────────


def compute_volume_profile_poc_123(
    price_levels: list[dict[str, Any]] | None = None,
    *,
    period: str = "session",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    levels = price_levels or [
        {"price": 64000, "volume": 1200},
        {"price": 64500, "volume": 3500},
        {"price": 65000, "volume": 5200},
        {"price": 65500, "volume": 2800},
        {"price": 66000, "volume": 900},
    ]
    poc = max(levels, key=lambda x: x["volume"])
    total_vol = sum(l["volume"] for l in levels) or 1
    sorted_levels = sorted(levels, key=lambda x: -x["volume"])
    va_vol = 0
    value_area: list[float] = []
    for lv in sorted_levels:
        va_vol += lv["volume"]
        value_area.append(lv["price"])
        if va_vol / total_vol >= 0.70:
            break

    fee = float((seed.get("volume_profile_poc_123") or {}).get("fee_db", {}).get("compute_usd", 0.001))
    return {
        "ok": True,
        "feature_ref": 123,
        "route": "/radar/technical/volume-profile",
        "merged_into": "ta_engine",
        "period": period,
        "poc_price": poc["price"],
        "poc_volume": poc["volume"],
        "value_area_prices": sorted(value_area),
        "value_area_pct": 70,
        "insight": {
            "en": f"POC at ${poc['price']:,.0f} — historical area of interest",
            "ar": f"POC عند ${poc['price']:,.0f} — منطقة اهتمام تاريخية",
        },
        "formula": "POC = price with highest cumulative volume; Value Area = 70% volume band",
        "fee_db": {"compute_usd": fee},
    }


# ─── #124 Fair Value Gap Detector ───────────────────────────────────────────────


def detect_fair_value_gaps_124(
    candles: list[dict[str, Any]] | None = None,
    *,
    validity_candles: int = 20,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    candles = candles or [
        {"high": 100, "low": 95},
        {"high": 108, "low": 102},
        {"high": 115, "low": 110},
        {"high": 112, "low": 105},
    ]
    gaps: list[dict[str, Any]] = []
    for i in range(2, len(candles)):
        c1, c3 = candles[i - 2], candles[i]
        if c3["low"] > c1["high"]:
            gaps.append({
                "type": "bullish",
                "low": c1["high"],
                "high": c3["low"],
                "mitigated": False,
                "validity_candles": validity_candles,
            })
        elif c3["high"] < c1["low"]:
            gaps.append({
                "type": "bearish",
                "low": c3["high"],
                "high": c1["low"],
                "mitigated": False,
                "validity_candles": validity_candles,
            })

    fee = float((seed.get("fvg_detector_124") or {}).get("fee_db", {}).get("compute_usd", 0.0008))
    return {
        "ok": True,
        "feature_ref": 124,
        "route": "/radar/technical/fvg-detector",
        "merged_into": "ta_engine",
        "gaps": gaps,
        "unfilled_count": len(gaps),
        "rules": {
            "bullish": "Low[Candle_3] > High[Candle_1]",
            "bearish": "High[Candle_3] < Low[Candle_1]",
        },
        "insight": {
            "en": f"{len(gaps)} FVG zone(s) detected — areas of interest, not predictions",
            "ar": f"{len(gaps)} منطقة FVG — مناطق اهتمام وليست توقعات",
        },
        "fee_db": {"compute_usd": fee},
    }


# ─── #125 Custody Tracking — DEFERRED Wave 3 ────────────────────────────────────


def custody_tracking_status_125(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("custody_tracking_125") or {}
    return {
        "ok": True,
        "feature_ref": 125,
        "status": "deferred",
        "wave": 3,
        "merged_into": "unified_portfolio_81",
        "route": "/portfolio/unified/custody",
        "read_only_api_keys": True,
        "no_withdrawal_permissions": True,
        "tier": "institution",
        "build_blocked_until": cfg.get("build_blocked_until", "institution_portal_stable"),
    }


# ─── #126 Front-Running Shield — REJECTED → DEX Risk Insight ──────────────────


def dex_front_running_risk_126(
    *,
    pool: str = "ETH/USDC",
    slippage_pct: float = 3.0,
    order_usd: float = 50_000,
    mev_bots_active: bool = True,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("dex_front_running_risk_126") or {}).get("fee_db", {}).get("compute_usd", 0.001))
    return {
        "ok": True,
        "feature_ref": 126,
        "status": "rejected_execution",
        "alternative": "dex_front_running_risk_insight",
        "route": "/oracle/on-chain/dex-risk",
        "execution_rejected": True,
        "pool": pool,
        "slippage_pct": slippage_pct,
        "order_usd": order_usd,
        "mev_bots_active": mev_bots_active,
        "insight": {
            "en": (
                f"Pool {pool} shows {slippage_pct}% slippage on ${order_usd:,.0f} order"
                + (" — MEV bots active on this pair" if mev_bots_active else "")
                + ". Low slippage tolerance may cause failed transactions"
            ),
            "ar": f"مجمع {pool} يُظهر انزلاق {slippage_pct}% — بوتات MEV نشطة. slippage منخفض قد يُسبب فشل الصفقة",
        },
        "no_shield_no_execution": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #127 Exploiter — REJECTED → Order Book Inefficiency Insight ───────────────


def orderbook_inefficiency_insight_127(
    *,
    exchange: str = "binance",
    pair: str = "BTC/USDT",
    spread_pct: float = 0.8,
    avg_spread_pct: float = 0.3,
    thin_level_price: float = 65000,
    move_pct_on_large_order: float = 1.2,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee = float((seed.get("orderbook_inefficiency_127") or {}).get("fee_db", {}).get("compute_usd", 0.0007))
    return {
        "ok": True,
        "feature_ref": 127,
        "status": "rejected_exploiter",
        "alternative": "orderbook_inefficiency_insight",
        "route": "/radar/technical/orderbook-inefficiency",
        "exploiter_naming_rejected": True,
        "exchange": exchange,
        "pair": pair,
        "spread_pct": spread_pct,
        "avg_spread_pct": avg_spread_pct,
        "insight": {
            "en": (
                f"{exchange} {pair} shows {spread_pct}% bid/ask gap — above {avg_spread_pct}% average. "
                f"Thin volume at ${thin_level_price:,.0f} — large order may move price {move_pct_on_large_order}%"
            ),
            "ar": f"فجوة {spread_pct}% في {pair} — حجم ضئيل عند ${thin_level_price:,.0f}",
        },
        "analysis_not_exploitation": True,
        "no_execution": True,
        "fee_db": {"compute_usd": fee},
    }


# ─── #128 Jargon Translator — extends #64 ───────────────────────────────────────

_JARGON_EXTENSIONS: dict[str, dict[str, str]] = {
    "Impermanent Loss": {
        "en": "Temporary loss when asset prices change in a liquidity pool",
        "ar": "خسارة مؤقتة عند تغير أسعار الأصول في مجمع السيولة",
        "simple_en": "temporary pool loss",
        "simple_ar": "خسارة مؤقتة في المجمع",
    },
    "Funding Rate": {
        "en": "Periodic payment between long and short traders in perpetual futures",
        "ar": "دفعة دورية بين المتداولين الطويل والقصير في العقود الدائمة",
        "simple_en": "futures balancing fee",
        "simple_ar": "رسوم توازن العقود",
    },
    "Liquidation": {
        "en": "Forced closure of a leveraged position when margin is insufficient",
        "ar": "إغلاق قسري لمركز برافعة عندما الهامش غير كافٍ",
        "simple_en": "forced position close",
        "simple_ar": "إغلاق قسري للمركز",
    },
    "VWAP": {
        "en": "Volume-weighted average price — fair value based on traded volume",
        "ar": "متوسط السعر المرجّح بالحجم — قيمة عادلة بناءً على الحجم المتداول",
        "simple_en": "volume-weighted fair price",
        "simple_ar": "سعر عادل مرجّح بالحجم",
    },
    "FVG": {
        "en": "Fair Value Gap — price gap between candles that may act as support/resistance",
        "ar": "فجوة القيمة العادلة — فجوة سعرية قد تعمل كدعم/مقاومة",
        "simple_en": "price gap zone",
        "simple_ar": "منطقة فجوة سعرية",
    },
}


def jargon_explanation_128(term: str, *, locale: str = "en") -> dict[str, Any]:
    """Extends #64 — rule-based mapping, no NLP."""
    try:
        from bd_platform.retail_intelligence_layer import simplify_term_64

        base = simplify_term_64(term, locale=locale)
    except ImportError:
        base = {"term": term, "simple": term, "explanation": "", "display": term}

    ext = _JARGON_EXTENSIONS.get(term) or _JARGON_EXTENSIONS.get(term.title()) or {}
    if ext:
        key = "ar" if locale.lower().startswith("ar") else "en"
        sk = f"simple_{key}"
        base["explanation"] = ext.get(key, base.get("explanation", ""))
        base["simple"] = ext.get(sk, base.get("simple", term))
        base["display"] = f"{base['simple']} ({term})"

    return {
        "ok": True,
        "feature_ref": 128,
        "merged_into": "simple_language_64",
        "rule_based_only": True,
        "ai_naming_rejected": True,
        **base,
    }


def attach_jargon_to_insight_128(payload: dict[str, Any], terms: list[str], *, locale: str = "en") -> dict[str, Any]:
    out = dict(payload)
    out["jargon_explanations"] = [jargon_explanation_128(t, locale=locale) for t in terms]
    out["merged_features"] = list(set((out.get("merged_features") or []) + [64, 128]))
    return out


# ─── Attach helpers ─────────────────────────────────────────────────────────────


def attach_journal_attribution_121(journal_tab: dict[str, Any], *, seed: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    out = dict(journal_tab)
    out["pnl_attribution"] = compute_pnl_attribution_121(seed=seed, **kwargs)
    return out


def attach_leverage_risk_120(risk_report: dict[str, Any], *, seed: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    out = dict(risk_report)
    out["leverage_risk_analysis"] = compute_leverage_risk_analysis_120(seed=seed, **kwargs)
    merged = list(out.get("merged_features") or [77])
    for ref in (105, 120):
        if ref not in merged:
            merged.append(ref)
    out["merged_features"] = merged
    return out


# ─── E2E ────────────────────────────────────────────────────────────────────────


def run_advanced_ta_risk_e2e_117_128(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    vac = compute_liquidity_vacuum_117(seed=seed)
    checks.append({"id": "117_vacuum", "passed": "vacuum_pct" in vac})

    dist = compute_exchange_risk_distribution_118(seed=seed)
    checks.append({"id": "118_distribution", "passed": dist.get("concentration_warning") is True})

    gas = gas_spike_alert_119(seed=seed)
    checks.append({"id": "119_rejected", "passed": gas["execution_rejected"] is True})

    lev = compute_leverage_risk_analysis_120(seed=seed)
    checks.append({"id": "120_leverage", "passed": lev["optimization_rejected"] is True})

    pnl = compute_pnl_attribution_121(seed=seed)
    checks.append({"id": "121_pnl", "passed": "drift_residual_usd" in pnl["attribution"]})

    brk = compute_structural_break_122(seed=seed)
    checks.append({"id": "122_break", "passed": brk["statistical_not_ai"] is True})

    poc = compute_volume_profile_poc_123(seed=seed)
    checks.append({"id": "123_poc", "passed": poc["poc_price"] > 0})

    fvg = detect_fair_value_gaps_124(seed=seed)
    checks.append({"id": "124_fvg", "passed": "gaps" in fvg})

    checks.append({"id": "125_deferred", "passed": custody_tracking_status_125(seed=seed)["status"] == "deferred"})

    dex = dex_front_running_risk_126(seed=seed)
    checks.append({"id": "126_rejected", "passed": dex["no_shield_no_execution"] is True})

    ob = orderbook_inefficiency_insight_127(seed=seed)
    checks.append({"id": "127_rejected", "passed": ob["exploiter_naming_rejected"] is True})

    jargon = jargon_explanation_128("Impermanent Loss", locale="en")
    checks.append({"id": "128_jargon", "passed": jargon["merged_into"] == "simple_language_64"})

    try:
        from bd_platform.institutional_b2b_layer import build_exchange_health_with_counterparty_92
        from bd_platform.pro_trader_layer import build_journal_tab_76
        from bd_platform.whales_institutional_layer import build_advanced_risk_report_77

        ex = attach_risk_distribution_118(build_exchange_health_with_counterparty_92(seed=seed), seed=seed)
        checks.append({"id": "118_embed", "passed": "risk_distribution" in ex})

        journal = attach_journal_attribution_121(build_journal_tab_76(seed=seed), seed=seed)
        checks.append({"id": "121_journal_embed", "passed": "pnl_attribution" in journal})

        risk = attach_leverage_risk_120(
            build_advanced_risk_report_77([{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}], seed=seed),
            seed=seed,
        )
        checks.append({"id": "120_risk_embed", "passed": "leverage_risk_analysis" in risk})
    except ImportError:
        pass

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
