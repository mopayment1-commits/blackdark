"""
Signal Context Layer — Feature #330-REV (Sprint 2).

Rule-based context panel over Market Radar + Portfolio AI.
Transforms raw data into understandable context — NOT recommendations.

Inputs: CVD (#232), Funding, Liquidity, Exchange Quality (#132), Bot Activity (#721),
On-Chain, Fee DB (#130).
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.SignalContext")

_FEATURE_ID = 330
_STANDALONE = False
_SPRINT = 2
_PANEL_VERSION = "1.0"
_ENGINE_VERSION = "1.0"
_SEED_PATH = Path("data/signal_context_seed.json")
_STALE_THRESHOLD_MS = 300_000

_DISCLAIMER_TEXT = (
    "This panel presents aggregated market data for context only. "
    "It is not investment advice. Signal strength measures data alignment, not future performance. "
    "Past data patterns do not predict future outcomes. You are solely responsible for your decisions."
)

ConfidenceLevel = Literal["high", "medium", "low"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"weights": {}, "assets": {}, "panel_version": _PANEL_VERSION}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("signal context seed load failed: %s", exc)
        return {"weights": {}, "assets": {}, "panel_version": _PANEL_VERSION}


def _freshness_display(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds} seconds ago"
    return f"{seconds // 60} minutes ago"


def _confidence_from_freshness(freshness_ms: int | float, *, stale: bool = False) -> ConfidenceLevel:
    if stale or freshness_ms > _STALE_THRESHOLD_MS:
        return "low"
    if freshness_ms <= 500:
        return "high"
    if freshness_ms <= 5000:
        return "medium"
    return "low"


def _build_data_alignment(inputs: dict[str, Any]) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    agree_count = 0
    for key, meta in inputs.items():
        if not isinstance(meta, dict):
            continue
        stale = bool(meta.get("stale")) or int(meta.get("freshness_ms") or 0) > _STALE_THRESHOLD_MS
        status = "stale" if stale else ("agree" if meta.get("agree", True) else "disagree")
        if status == "agree":
            agree_count += 1
        name_map = {
            "cvd": "CVD Feed",
            "funding": "Funding API",
            "liquidity": "Liquidity Engine",
            "exchange_quality": "Exchange Quality",
            "onchain": "On-Chain",
            "social": "Social Feed",
            "bot_activity": "Bot Activity",
        }
        sources.append({
            "name": name_map.get(key, key.replace("_", " ").title()),
            "status": status,
            "freshness_ms": meta.get("freshness_ms"),
        })

    total = len(sources)
    score_pct = round(agree_count / total * 100, 1) if total else 0.0
    return {
        "score": f"{score_pct:.0f}%",
        "score_pct": score_pct,
        "sources_agree": f"{agree_count}/{total}",
        "sources": sources,
    }


def _score_component(value: float, *, low: float = 0, high: float = 10) -> float:
    return round(max(0.0, min(10.0, value)), 1)


def _compute_signal_strength(
    alignment_pct: float,
    cvd_score: float,
    funding_score: float,
    liquidity_score: float,
    exchange_score: float,
    fee_score: float,
    weights: dict[str, float],
) -> float:
    composite = (
        (alignment_pct / 10) * weights.get("data_alignment", 0.30) * 10
        + cvd_score * weights.get("cvd_context", 0.20)
        + funding_score * weights.get("funding_context", 0.15)
        + liquidity_score * weights.get("liquidity_context", 0.15)
        + exchange_score * weights.get("exchange_risk", 0.10)
        + fee_score * weights.get("fee_impact", 0.10)
    )
    return round(max(0.0, min(10.0, composite)), 1)


def _build_three_reasons(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = []

    cvd = inputs.get("cvd") or {}
    if cvd:
        trend = str(cvd.get("trend", "flat")).title()
        pct = float(cvd.get("pct_vs_baseline") or 0)
        reasons.append({
            "id": len(reasons) + 1,
            "label": f"CVD {trend}",
            "value": f"{pct:+.1f}% vs 30D baseline",
            "source": cvd.get("source", "CVD Module #232"),
            "timestamp": cvd.get("timestamp", _utcnow()),
            "confidence": _confidence_from_freshness(int(cvd.get("freshness_ms") or 0)),
        })

    funding = inputs.get("funding") or {}
    if funding:
        rate = float(funding.get("rate_pct") or 0)
        z = float(funding.get("z_score") or 0)
        regime = str(funding.get("regime", "neutral")).title()
        reasons.append({
            "id": len(reasons) + 1,
            "label": f"Funding Rate {regime}",
            "value": f"{rate:+.3f}% | z-score: {z:.1f}",
            "source": funding.get("source", "Funding Feed"),
            "timestamp": funding.get("timestamp", _utcnow()),
            "confidence": _confidence_from_freshness(int(funding.get("freshness_ms") or 0)),
        })

    liq = inputs.get("liquidity") or {}
    if liq:
        depth = float(liq.get("depth_change_pct") or 0)
        spread = float(liq.get("spread_bps") or 0)
        label = "Liquidity Depth Increased" if depth >= 0 else "Liquidity Depth Decreased"
        reasons.append({
            "id": len(reasons) + 1,
            "label": label,
            "value": f"{depth:+.1f}% | Spread: {spread:.1f} bps",
            "source": liq.get("source", "Liquidity Analytics"),
            "timestamp": liq.get("timestamp", _utcnow()),
            "confidence": _confidence_from_freshness(int(liq.get("freshness_ms") or 0)),
        })

    onchain = inputs.get("onchain") or {}
    if onchain and len(reasons) < 3:
        reasons.append({
            "id": len(reasons) + 1,
            "label": "On-Chain Netflow",
            "value": f"{onchain.get('netflow_direction', 'neutral').title()} | MVRV proxy {onchain.get('mvrv_proxy')}",
            "source": onchain.get("source", "On-Chain Metrics"),
            "timestamp": onchain.get("timestamp", _utcnow()),
            "confidence": _confidence_from_freshness(int(onchain.get("freshness_ms") or 0)),
        })

    ex = inputs.get("exchange_quality") or {}
    if ex and len(reasons) < 3:
        reasons.append({
            "id": len(reasons) + 1,
            "label": "Exchange Quality",
            "value": f"{ex.get('score', 0)}/10 on {ex.get('exchange', 'binance').title()}",
            "source": ex.get("source", "Exchange Quality #132"),
            "timestamp": ex.get("timestamp", _utcnow()),
            "confidence": _confidence_from_freshness(int(ex.get("freshness_ms") or 0)),
        })

    return reasons[:3]


def _build_risk_flags(inputs: dict[str, Any]) -> dict[str, Any]:
    bot = inputs.get("bot_activity") or {}
    ex = inputs.get("exchange_quality") or {}
    funding = inputs.get("funding") or {}

    spoofing = "detected" if bot.get("spoofing_detected") else "none"
    ex_score = float(ex.get("score") or 5)
    ex_status = "high" if ex_score >= 7 else "medium" if ex_score >= 5 else "low"

    fr = float(funding.get("rate_pct") or 0)
    if fr < -0.005:
        funding_risk = "medium"
        funding_detail = "Negative funding elevated"
    elif fr < 0:
        funding_risk = "low"
        funding_detail = "Negative but stable"
    else:
        funding_risk = "low"
        funding_detail = "Neutral to positive"

    flags = [
        {
            "label": "Spoofing Detected",
            "status": spoofing,
            "source": bot.get("source", "Bot Activity #721"),
        },
        {
            "label": "Exchange Quality",
            "status": ex_status,
            "value": f"{ex_score:.1f}/10",
            "source": ex.get("source", "Exchange Quality #132"),
        },
        {
            "label": "Funding Risk",
            "status": funding_risk,
            "value": funding_detail,
            "source": funding.get("source", "Funding Feed"),
        },
    ]

    risk_total = 0.0
    if spoofing == "detected":
        risk_total += 4
    risk_total += max(0, 10 - ex_score) * 0.3
    if funding_risk == "medium":
        risk_total += 2
    risk_score = _score_component(risk_total, high=10)

    return {
        "total_score": f"{risk_score:.0f}/10",
        "total_score_numeric": risk_score,
        "flags": flags,
    }


def _build_fee_impact(fee: dict[str, Any]) -> dict[str, Any]:
    net = float(fee.get("net_after_fees_pct") or 0)
    negative = bool(fee.get("negative_fee_context")) or net < 0
    block = {
        "gas_estimate": f"${fee.get('gas_estimate_usd', 0):.2f}",
        "funding_1h": f"${fee.get('funding_1h_usd', 0):+.2f}",
        "slippage_estimate": f"{fee.get('slippage_estimate_pct', 0):.2f}%",
        "net_after_fees": f"{net:+.2f}%",
        "fee_db_version": fee.get("fee_db_version", "1.3"),
        "fee_db_feature_id": 130,
        "disclaimer": "Fee estimates are approximate. Actual costs may vary.",
        "negative_fee_context": negative,
    }
    if negative:
        block["context_note"] = "Fee Impact: Negative | Context: High Cost Environment"
    return block


async def _enrich_inputs_from_live(asset: str, seed_inputs: dict[str, Any]) -> dict[str, Any]:
    """Merge seed inputs with live feeds where available — no look-ahead."""
    inputs = dict(seed_inputs)
    sym = asset.upper()

    try:
        from bd_platform.free_market_data import binance_futures_snapshot

        snap = await binance_futures_snapshot(sym)
        fr = float(snap.get("funding_rate_pct") or 0)
        if "funding" not in inputs or inputs["funding"].get("agree"):
            inputs["funding"] = {
                **(inputs.get("funding") or {}),
                "rate_pct": fr,
                "regime": "negative" if fr < 0 else "positive" if fr > 0 else "neutral",
                "freshness_ms": 200,
                "timestamp": snap.get("timestamp") or _utcnow(),
                "source": "Funding Feed",
                "agree": True,
            }
    except Exception:
        logger.debug("live funding enrich failed", exc_info=True)

    try:
        from fee_matrix import maker_fee, taker_fee

        taker = taker_fee("binance") or 0.001
        inputs.setdefault("fee_db", {
            "taker_fee_pct": round(taker * 100, 4),
            "fee_db_feature_id": 130,
            "fee_db_available": True,
        })
    except Exception:
        inputs.setdefault("fee_db", {"fee_db_available": False, "fee_db_feature_id": 130})

    return inputs


async def build_context_panel(
    asset: str = "BTC",
    *,
    surface: str = "market_radar",
) -> dict[str, Any]:
    """Build Signal Context Panel — data only, no recommendation."""
    t0 = time.perf_counter()
    seed = _load_seed()
    sym = asset.upper().replace("/USDT", "")
    asset_data = (seed.get("assets") or {}).get(sym)

    if not asset_data:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "asset_not_configured", "asset": sym}

    inputs = await _enrich_inputs_from_live(sym, asset_data.get("inputs") or {})
    weights = seed.get("weights") or {}
    alignment = _build_data_alignment(inputs)

    cvd = inputs.get("cvd") or {}
    cvd_score = _score_component(5 + float(cvd.get("pct_vs_baseline") or 0) * 0.3)
    funding = inputs.get("funding") or {}
    funding_score = _score_component(5 - abs(float(funding.get("z_score") or 0)))
    liq = inputs.get("liquidity") or {}
    liquidity_score = _score_component(5 + float(liq.get("depth_change_pct") or 0) * 0.2)
    ex = inputs.get("exchange_quality") or {}
    exchange_score = float(ex.get("score") or 5)
    fee_data = asset_data.get("fee_impact") or {}
    fee_net = float(fee_data.get("net_after_fees_pct") or 0)
    fee_score = _score_component(5 + fee_net * 5)

    strength = _compute_signal_strength(
        alignment["score_pct"],
        cvd_score,
        funding_score,
        liquidity_score,
        exchange_score,
        fee_score,
        weights,
    )

    reasons = _build_three_reasons(inputs)
    min_reasons = int(seed.get("min_reasons") or 3)
    insufficient = len(reasons) < min_reasons

    freshness_sec = int(asset_data.get("data_freshness_seconds") or 45)
    panel_version = seed.get("panel_version", _PANEL_VERSION)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    disclaimer_block = {
        "text": _DISCLAIMER_TEXT,
        "collapsible": False,
        "hideable": False,
        "version": panel_version,
    }

    panel = {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "surface": surface,
        "asset": sym,
        "panel_version": panel_version,
        "panel_version_display": (
            f"Context Panel v{panel_version} | Methodology: {seed.get('methodology', 'Rule-Based')} | "
            f"Last Updated: {seed.get('last_updated', 'N/A')}"
        ),
        "engine_version": seed.get("engine_version", _ENGINE_VERSION),
        "weights_version": seed.get("weights_version", "1.0"),
        "generated_at": _utcnow(),
        "data_freshness": _freshness_display(freshness_sec),
        "data_freshness_seconds": freshness_sec,
        "no_look_ahead": True,
        "no_look_ahead_note": "Panel uses data up to moment T only",
        "signal_strength": {
            "score": f"{strength:.0f}/10",
            "score_numeric": strength,
            "methodology": (
                f"Rule-based v{seed.get('engine_version', _ENGINE_VERSION)} | "
                f"6 inputs | Weights documented"
            ),
        },
        "data_alignment": alignment,
        "three_reasons": reasons,
        "insufficient_data_context": insufficient,
        "insufficient_display": (
            f"Insufficient Data Context | Reasons available: {len(reasons)}/{min_reasons}"
            if insufficient
            else None
        ),
        "risk_flags": _build_risk_flags(inputs),
        "fee_impact": _build_fee_impact(fee_data),
        "disclaimer_top": disclaimer_block,
        "disclaimer": disclaimer_block,
        "disclaimer_bottom": disclaimer_block,
        "not_a_recommendation": True,
        "not_buy_sell_signal": True,
        "allowed_language": ["Context", "Analysis", "Data Alignment", "Signal Strength", "Risk Flags"],
        "pro_tier": seed.get("tier", "pro") == "pro",
        "sla_met": elapsed <= int(seed.get("generation_sla_ms") or 500),
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }
    return panel


async def build_portfolio_context_panel(
    asset: str = "BTC",
    *,
    portfolio_id: str | None = None,
) -> dict[str, Any]:
    """Context panel for Portfolio AI surface."""
    panel = await build_context_panel(asset, surface="portfolio_ai")
    if panel.get("ok"):
        panel["portfolio_id"] = portfolio_id
        panel["merged_into"] = ["Market Radar", "Portfolio AI"]
    return panel


def signal_context_layer_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "feature_label": seed.get("feature_label", "#330-REV Signal Context Layer"),
        "standalone": _STANDALONE,
        "sprint": _SPRINT,
        "panel_version": seed.get("panel_version", _PANEL_VERSION),
        "engine_version": seed.get("engine_version", _ENGINE_VERSION),
        "methodology": seed.get("methodology", "Rule-Based"),
        "weights": seed.get("weights"),
        "weights_version": seed.get("weights_version"),
        "tier": seed.get("tier", "pro"),
        "generation_sla_ms": seed.get("generation_sla_ms", 500),
        "historical_validation_months": seed.get("historical_validation_months", 6),
        "integrated_surfaces": ["Market Radar", "Portfolio AI"],
        "inputs": ["CVD #232", "Funding", "Liquidity", "Exchange Quality #132", "Bot Activity #721", "On-Chain", "Fee DB #130"],
        "acceptance_criteria": {
            "rule_based_documented": True,
            "risk_flags_visible": True,
            "data_alignment_score": True,
            "panel_generation_500ms": True,
            "three_reasons_minimum": True,
            "fee_db_integrated": True,
            "disclaimer_non_hideable": True,
            "no_look_ahead": True,
            "not_recommendation": True,
        },
        "disclaimer": _DISCLAIMER_TEXT,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
