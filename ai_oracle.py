"""
BLACKDARK — AI Intelligence & Evaluation Layer (Phase 4: Points 15, 16, 17, & 18).

Scores arbitrage opportunities deterministically, generates oracle verdicts,
and produces structured explanations before persistence.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Literal, Optional

import aiohttp
from pydantic import BaseModel, Field

import config
from database import insert_evaluated_opportunity
from obi_predictor import get_obi_for_asset
from onchain_tracker import (
    get_onchain_status_for_asset,
    inject_oracle_onchain_analytics,
)
from macro_correlations import apply_macro_score_weight, macro_score_weight
from sentiment_engine import (
    build_sentiment_panic_warning,
    get_sentiment_index_for_asset,
    is_extreme_negative_sentiment,
    sentiment_panic_penalty_for_asset,
)
from oracle_data_hub import hub_score_adjustment, synthesize_with_free_llm_chain

logger = logging.getLogger("BLACKDARK.AIOracle")

OpportunityKind = Literal[
    "cross_exchange",
    "triangular",
    "spot_futures",
    "funding",
]
OracleVerdict = Literal["Buy Now", "Do Not Touch"]


class OpportunityMetrics(BaseModel):
    asset: str
    kind: OpportunityKind
    net_profit_usdt: float
    net_profit_percent: float
    total_slippage_bps: float = Field(ge=0)
    gross_spread_bps: float = 0.0
    basis_bps: float = 0.0
    funding_spread_bps: float = 0.0
    quote_amount: float = Field(gt=0)


class OpportunityExplanation(BaseModel):
    kind: OpportunityKind
    asset: str
    summary: str
    reasons: list[str]
    risk_factors: list[str]
    confidence_percent: float = Field(ge=0, le=100)


class OracleResponse(BaseModel):
    verdict: OracleVerdict
    sentence: str


class EvaluatedOpportunity(BaseModel):
    kind: OpportunityKind
    asset: str
    opportunity_score: float = Field(ge=0, le=100)
    net_profit_usdt: float
    oracle: OracleResponse
    explanation: OpportunityExplanation
    payload: dict[str, Any]


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(upper, value))


def _asset_from_symbol(symbol: str) -> str:
    return symbol.split("/")[0]


def extract_metrics(opportunity: Any, kind: OpportunityKind) -> OpportunityMetrics:
    """Normalize heterogeneous opportunity models into scoring metrics."""
    if kind == "cross_exchange":
        return OpportunityMetrics(
            asset=_asset_from_symbol(opportunity.symbol),
            kind=kind,
            net_profit_usdt=float(opportunity.net_profit_usdt),
            net_profit_percent=float(opportunity.net_profit_percent),
            total_slippage_bps=float(opportunity.total_slippage_bps),
            gross_spread_bps=float(opportunity.gross_spread_bps),
            quote_amount=float(opportunity.quote_amount),
        )

    if kind == "triangular":
        anchor_coin = config.TRIANGLE_ANCHOR
        path = str(opportunity.path)
        asset = path.split("->")[1] if "->" in path else anchor_coin
        return OpportunityMetrics(
            asset=asset,
            kind=kind,
            net_profit_usdt=float(opportunity.net_profit_usdt),
            net_profit_percent=float(opportunity.net_profit_percent),
            total_slippage_bps=float(opportunity.total_slippage_bps),
            gross_spread_bps=float(opportunity.gross_spread_bps),
            quote_amount=float(opportunity.quote_amount),
        )

    if kind == "spot_futures":
        return OpportunityMetrics(
            asset=_asset_from_symbol(opportunity.symbol),
            kind=kind,
            net_profit_usdt=float(opportunity.net_profit_usdt),
            net_profit_percent=float(opportunity.net_profit_percent),
            total_slippage_bps=float(opportunity.total_slippage_bps),
            gross_spread_bps=float(opportunity.basis_bps),
            basis_bps=float(opportunity.basis_bps),
            quote_amount=float(opportunity.quote_amount),
        )

    return OpportunityMetrics(
        asset=_asset_from_symbol(opportunity.symbol),
        kind=kind,
        net_profit_usdt=float(opportunity.net_yield_usdt),
        net_profit_percent=float(opportunity.net_yield_percent),
        total_slippage_bps=float(getattr(opportunity, "total_slippage_bps", 0.0) or 0.0),
        gross_spread_bps=float(opportunity.funding_spread_bps),
        funding_spread_bps=float(opportunity.funding_spread_bps),
        quote_amount=float(opportunity.quote_amount),
    )


def calculate_opportunity_score(
    opportunity: Any,
    kind: OpportunityKind,
    institutional_context: dict[str, Any] | None = None,
) -> float:
    """
    Deterministic 0-100 score from net profit, liquidity depth, and stability.

    Weights: profit 40%, liquidity 35%, stability 25%.
    """
    metrics = extract_metrics(opportunity, kind)

    profit_score = _clamp(
        (metrics.net_profit_percent / config.AI_ORACLE_PROFIT_REFERENCE_PCT) * 100
    )

    liquidity_score = _clamp(
        100 - (metrics.total_slippage_bps / config.AI_ORACLE_SLIPPAGE_REFERENCE_BPS) * 100
    )

    stability_signal = max(
        abs(metrics.gross_spread_bps),
        abs(metrics.basis_bps),
        abs(metrics.funding_spread_bps),
    )
    slippage_denominator = max(metrics.total_slippage_bps, 1.0)
    stability_ratio = stability_signal / slippage_denominator
    stability_score = _clamp(stability_ratio * 20)

    from weight_aggregator import apply_modal_adjustments, get_core_score_weights

    core = get_core_score_weights()
    final_score = (
        profit_score * core["profit"]
        + liquidity_score * core["liquidity"]
        + stability_score * core["stability"]
    )

    if institutional_context:
        compound = get_sentiment_index_for_asset(metrics.asset, institutional_context)
        if is_extreme_negative_sentiment(compound):
            final_score -= sentiment_panic_penalty_for_asset(metrics.asset, institutional_context)
        final_score, _breakdown = apply_modal_adjustments(
            final_score,
            metrics.asset,
            institutional_context,
        )

    if kind == "funding":
        convergence_delta = float(
            getattr(opportunity, "predictive_convergence_score_delta", 0.0) or 0.0
        )
        final_score += convergence_delta

    final_score = apply_macro_score_weight(final_score, institutional_context)

    if institutional_context:
        hub = institutional_context.get("oracle_data_hub") or {}
        if hub.get("enabled"):
            hub_delta, _, _ = hub_score_adjustment(metrics.asset, hub)
            final_score += hub_delta

    return round(_clamp(final_score), 2)


def explain_opportunity(
    opportunity: Any,
    kind: OpportunityKind,
    opportunity_score: float,
    institutional_context: dict[str, Any] | None = None,
) -> OpportunityExplanation:
    """Break down technical drivers and produce a confidence percentage."""
    metrics = extract_metrics(opportunity, kind)
    reasons: list[str] = []
    risks: list[str] = []

    reasons.append(
        f"Net edge after costs: ${metrics.net_profit_usdt:.4f} "
        f"({metrics.net_profit_percent:.4f}%) on ${metrics.quote_amount:.2f} notional."
    )
    reasons.append(
        f"Depth-walk slippage: {metrics.total_slippage_bps:.2f} bps "
        f"(lower is better for executable size)."
    )

    if kind == "cross_exchange":
        reasons.append(
            f"Cross-venue spread: buy {opportunity.buy_exchange} / "
            f"sell {opportunity.sell_exchange} at "
            f"{opportunity.gross_spread_bps:.2f} bps gross."
        )
        risks.append(
            f"Withdrawal fee drag: ${float(opportunity.withdrawal_fee_usdt):.4f}."
        )
    elif kind == "triangular":
        reasons.append(
            f"Triangular loop {opportunity.path} on {opportunity.exchange} "
            f"at {opportunity.gross_spread_bps:.2f} bps gross."
        )
        risks.append("Three-leg execution risk: one stale leg collapses the loop.")
    elif kind == "spot_futures":
        reasons.append(
            f"Spot-perp basis on {opportunity.exchange}: "
            f"{metrics.basis_bps:.2f} bps ({opportunity.direction})."
        )
        risks.append("Basis can mean-revert before both legs fill.")
    elif kind == "funding":
        reasons.append(
            f"Funding spread: long {opportunity.long_exchange} / "
            f"short {opportunity.short_exchange} at "
            f"{metrics.funding_spread_bps:.2f} bps."
        )
        risks.append("Funding rates reset each interval and can flip quickly.")
        sii_adj = float(getattr(opportunity, "sii_convergence_adjustment_usdt", 0.0) or 0.0)
        if sii_adj:
            reasons.append(
                f"SII convergence model: sector velocity adjustment ${sii_adj:+.4f}."
            )
        cvvd_buffer = float(getattr(opportunity, "institutional_risk_buffer_usdt", 0.0) or 0.0)
        cvvd_patterns = getattr(opportunity, "cvvd_risk_patterns", []) or []
        if cvvd_buffer > 0 and cvvd_patterns:
            risks.append(
                f"CVVD risk buffer applied (${cvvd_buffer:.4f}) due to "
                f"{', '.join(cvvd_patterns)}."
            )

    if institutional_context:
        alert_count = len(institutional_context.get("manipulation_alerts", [])) or len(
            institutional_context.get("whale_alerts", [])
        )
        if alert_count:
            reasons.append(
                f"CVVD radar: {alert_count} cross-venue manipulation signal(s) in latest sweep."
            )
        sector_flows = institutional_context.get("sector_inflow_index") or institutional_context.get(
            "sector_flows", []
        )
        asset_sector = config.SECTOR_MAP.get(metrics.asset)
        for flow in sector_flows:
            if flow.get("sector") == asset_sector:
                meta_raw = flow.get("metadata_json")
                meta = {}
                if isinstance(meta_raw, str):
                    try:
                        meta = json.loads(meta_raw)
                    except json.JSONDecodeError:
                        meta = {}
                sii = float(meta.get("sii_score") or flow.get("net_flow_usd") or 0.0)
                reasons.append(
                    f"Sector Inflow Index ({asset_sector}): SII {sii:.1f} "
                    f"(capital acceleration, not raw volume)."
                )
                break

    asset_obi = get_obi_for_asset(metrics.asset, institutional_context or {})
    if asset_obi is not None:
        reasons.append(f"Order book imbalance (OBI): {asset_obi:+.3f} across watched venues.")
    obi_warnings = (institutional_context or {}).get("obi_warnings") or []
    for warning in obi_warnings:
        if str(warning.get("asset") or "") != metrics.asset:
            continue
        risks.append(str(warning.get("message") or warning.get("warning_type") or "OBI warning"))
        break

    onchain_status = get_onchain_status_for_asset(metrics.asset, institutional_context or {})
    if onchain_status:
        bias = str(onchain_status.get("bias") or "neutral")
        net_flow = float(onchain_status.get("net_flow_usd") or 0.0)
        if bias == "accumulation":
            reasons.append(
                f"On-chain matrix: accumulation bias (${net_flow:+,.0f} net exchange outflow)."
            )
        elif bias == "distribution":
            risks.append(
                f"On-chain matrix: distribution risk (${net_flow:+,.0f} net exchange inflow)."
            )
        for signal in onchain_status.get("signals") or []:
            text = str(signal.get("message") or signal.get("signal_type") or "")
            if signal.get("signal_type") == "accumulation_signal":
                reasons.append(text)
            else:
                risks.append(text)
            break

    sentiment_index = float(
        (institutional_context or {}).get("sentiment_compound_index", {}).get(metrics.asset, 0.0)
    )
    if is_extreme_negative_sentiment(sentiment_index):
        risks.append(build_sentiment_panic_warning(metrics.asset, sentiment_index))
    elif abs(sentiment_index) > config.SENTIMENT_NEUTRAL_BAND:
        tone = "greed/FOMO" if sentiment_index > 0 else "fear/panic"
        reasons.append(
            f"5-minute news sentiment for {metrics.asset}: {sentiment_index:+.2f} ({tone})."
        )

    macro_regime = str((institutional_context or {}).get("macro_regime") or "")
    if macro_regime:
        macro_weight = macro_score_weight(institutional_context)
        dxy = float((institutional_context or {}).get("macro_dxy_score", 0.0))
        spx = float((institutional_context or {}).get("macro_spx_score", 0.0))
        buffer = float((institutional_context or {}).get("macro_volatility_buffer", 0.0))
        macro_line = (
            f"Macro regime: {macro_regime} | DXY {dxy:+.2f}% | SPX {spx:+.2f}% | "
            f"volatility buffer {buffer:.1f} bps | score weight x{macro_weight:.2f}."
        )
        if macro_regime == "Risk-Off":
            risks.append(macro_line)
        else:
            reasons.append(macro_line)

    hub = (institutional_context or {}).get("oracle_data_hub") or {}
    if hub.get("enabled"):
        _, hub_reasons, hub_risks = hub_score_adjustment(metrics.asset, hub)
        reasons.extend(hub_reasons[:4])
        risks.extend(hub_risks[:4])
        geo = hub.get("geo_news") or {}
        if geo.get("headlines"):
            top_geo = next(
                (h for h in geo["headlines"] if h.get("geopolitical")),
                geo["headlines"][0],
            )
            risks.append(
                f"Global headline watch: {top_geo.get('title', '')[:120]}"
            )

    if metrics.total_slippage_bps >= config.AI_ORACLE_SLIPPAGE_REFERENCE_BPS:
        risks.append("Slippage is elevated relative to the configured safety ceiling.")

    confidence = _clamp(
        opportunity_score * 0.55
        + liquidity_component(metrics.total_slippage_bps) * 0.25
        + profit_component(metrics.net_profit_percent) * 0.20
    )

    summary = (
        f"{metrics.asset} {kind.replace('_', ' ')} setup scores "
        f"{opportunity_score:.1f}/100 with {confidence:.1f}% confidence."
    )

    return OpportunityExplanation(
        kind=kind,
        asset=metrics.asset,
        summary=summary,
        reasons=reasons,
        risk_factors=risks,
        confidence_percent=round(confidence, 2),
    )


def liquidity_component(slippage_bps: float) -> float:
    return _clamp(100 - (slippage_bps / config.AI_ORACLE_SLIPPAGE_REFERENCE_BPS) * 100)


def profit_component(net_profit_percent: float) -> float:
    return _clamp((net_profit_percent / config.AI_ORACLE_PROFIT_REFERENCE_PCT) * 100)


def _rules_oracle(
    asset: str,
    opportunity_score: float,
    explanation: OpportunityExplanation,
) -> OracleResponse:
    actionable = (
        opportunity_score >= config.AI_ORACLE_MIN_SCORE
        and explanation.confidence_percent >= config.AI_ORACLE_MIN_CONFIDENCE
    )
    if actionable:
        reason = explanation.reasons[0] if explanation.reasons else "Positive net edge detected."
        return OracleResponse(
            verdict="Buy Now",
            sentence=f"Buy Now — {asset}: {reason}",
        )

    top_risk = explanation.risk_factors[0] if explanation.risk_factors else "Edge is too thin."
    return OracleResponse(
        verdict="Do Not Touch",
        sentence=f"Do Not Touch — {asset}: {top_risk}",
    )


async def _openai_oracle(
    asset: str,
    opportunity_score: float,
    explanation: OpportunityExplanation,
) -> Optional[OracleResponse]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    prompt = (
        "You are a disciplined crypto execution desk analyst. "
        "Return exactly one sentence starting with either 'Buy Now' or 'Do Not Touch' "
        "followed by an em dash and a concise reason.\n"
        f"Asset: {asset}\n"
        f"Score: {opportunity_score}\n"
        f"Summary: {explanation.summary}\n"
        f"Reasons: {' | '.join(explanation.reasons)}\n"
        f"Risks: {' | '.join(explanation.risk_factors)}"
    )

    payload = {
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": [
            {"role": "system", "content": "Reply with one sentence only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 80,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                data = await response.json()
        sentence = data["choices"][0]["message"]["content"].strip()
        verdict: OracleVerdict = (
            "Buy Now" if sentence.startswith("Buy Now") else "Do Not Touch"
        )
        return OracleResponse(verdict=verdict, sentence=sentence)
    except Exception as exc:
        logger.warning("OpenAI oracle fallback triggered: %s", exc)
        return None


async def _ollama_oracle(
    asset: str,
    opportunity_score: float,
    explanation: OpportunityExplanation,
) -> Optional[OracleResponse]:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "llama3.2")

    prompt = (
        "Return one sentence only. Start with 'Buy Now' or 'Do Not Touch', then em dash, "
        f"then reason. Asset={asset}, score={opportunity_score}, "
        f"summary={explanation.summary}"
    )

    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            ) as response:
                response.raise_for_status()
                data = await response.json()
        sentence = str(data.get("response", "")).strip().split("\n")[0]
        if not sentence:
            return None
        verdict: OracleVerdict = (
            "Buy Now" if sentence.startswith("Buy Now") else "Do Not Touch"
        )
        return OracleResponse(verdict=verdict, sentence=sentence)
    except Exception as exc:
        logger.warning("Ollama oracle fallback triggered: %s", exc)
        return None


async def get_single_sentence_oracle(
    asset: str,
    opportunity_score: float,
    explanation: OpportunityExplanation,
    institutional_context: dict[str, Any] | None = None,
) -> OracleResponse:
    """
    Return a one-sentence financial oracle verdict for an asset.

    Uses configured provider with graceful fallback to deterministic rules.
    """
    provider = os.getenv("AI_ORACLE_PROVIDER", config.AI_ORACLE_PROVIDER).lower()
    hub = (institutional_context or {}).get("oracle_data_hub") or {}

    if provider == "openai":
        llm = await _openai_oracle(asset, opportunity_score, explanation)
        if llm is not None:
            return llm
    elif provider == "ollama":
        llm = await _ollama_oracle(asset, opportunity_score, explanation)
        if llm is not None:
            return llm
    elif provider == "free_chain" and hub.get("enabled"):
        sentence = await synthesize_with_free_llm_chain(
            asset,
            opportunity_score,
            explanation.summary,
            hub,
        )
        if sentence:
            verdict: OracleVerdict = (
                "Buy Now" if sentence.startswith("Buy Now") else "Do Not Touch"
            )
            return OracleResponse(verdict=verdict, sentence=sentence)

    if hub.get("enabled"):
        sentence = await synthesize_with_free_llm_chain(
            asset,
            opportunity_score,
            explanation.summary,
            hub,
        )
        if sentence:
            verdict = "Buy Now" if sentence.startswith("Buy Now") else "Do Not Touch"
            return OracleResponse(verdict=verdict, sentence=sentence)

    return _rules_oracle(asset, opportunity_score, explanation)


async def evaluate_opportunity(
    opportunity: Any,
    kind: OpportunityKind,
    institutional_context: dict[str, Any] | None = None,
) -> EvaluatedOpportunity:
    """Score, explain, and oracle-wrap a single opportunity."""
    score = calculate_opportunity_score(opportunity, kind, institutional_context)
    explanation = explain_opportunity(opportunity, kind, score, institutional_context)
    oracle = await get_single_sentence_oracle(
        explanation.asset, score, explanation, institutional_context
    )
    oracle = OracleResponse(
        verdict=oracle.verdict,
        sentence=inject_oracle_onchain_analytics(
            oracle.sentence,
            explanation.asset,
            institutional_context,
        ),
    )
    metrics = extract_metrics(opportunity, kind)

    if hasattr(opportunity, "model_dump"):
        payload = opportunity.model_dump()
    else:
        payload = dict(opportunity)

    return EvaluatedOpportunity(
        kind=kind,
        asset=metrics.asset,
        opportunity_score=score,
        net_profit_usdt=metrics.net_profit_usdt,
        oracle=oracle,
        explanation=explanation,
        payload=payload,
    )


async def evaluate_and_store(
    opportunity: Any,
    kind: OpportunityKind,
    institutional_context: dict[str, Any] | None = None,
) -> EvaluatedOpportunity:
    """Evaluate an opportunity and persist the AI verdict to SQLite."""
    evaluated = await evaluate_opportunity(opportunity, kind, institutional_context)
    await insert_evaluated_opportunity(
        kind=evaluated.kind,
        asset=evaluated.asset,
        payload_json=json.dumps(evaluated.payload, separators=(",", ":")),
        opportunity_score=evaluated.opportunity_score,
        net_profit_usdt=evaluated.net_profit_usdt,
        oracle_verdict=evaluated.oracle.verdict,
        oracle_sentence=evaluated.oracle.sentence,
        explanation_json=evaluated.explanation.model_dump_json(),
        confidence_percent=evaluated.explanation.confidence_percent,
    )
    return evaluated


def log_evaluated_opportunity(evaluated: EvaluatedOpportunity) -> None:
    logger.info(
        "AI Oracle | %s %s | score=%.1f conf=%.1f%% | net=$%.4f | %s",
        evaluated.kind,
        evaluated.asset,
        evaluated.opportunity_score,
        evaluated.explanation.confidence_percent,
        evaluated.net_profit_usdt,
        evaluated.oracle.sentence,
    )
