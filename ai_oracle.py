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


def _economic_base_score(opportunity: Any, kind: OpportunityKind) -> tuple[float, OpportunityMetrics]:
    """Profit / liquidity / stability base (arb-specific economics)."""
    metrics = extract_metrics(opportunity, kind)
    from weight_aggregator import get_core_score_weights

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
    core = get_core_score_weights()
    base = (
        profit_score * core["profit"]
        + liquidity_score * core["liquidity"]
        + stability_score * core["stability"]
    )
    if kind == "funding":
        base += float(getattr(opportunity, "predictive_convergence_score_delta", 0.0) or 0.0)
    return base, metrics


def score_opportunity_with_breakdown(
    opportunity: Any,
    kind: OpportunityKind,
    institutional_context: dict[str, Any] | None = None,
) -> tuple[float, dict[str, Any], OpportunityMetrics]:
    """
    Unified arb scoring: economic base + shared multimodal post-processor.

    Macro is applied once inside regime modal weights (no double multiply).
    """
    from oracle_unified import apply_unified_adjustments

    base, metrics = _economic_base_score(opportunity, kind)
    change_24h = float(
        getattr(opportunity, "change_24h", 0.0)
        or (institutional_context or {}).get("change_24h", 0.0)
        or 0.0
    )
    quote_volume = float(
        getattr(opportunity, "quote_volume", 0.0)
        or getattr(opportunity, "quote_amount", 0.0)
        or metrics.quote_amount
        or 0.0
    )
    adjusted, breakdown = apply_unified_adjustments(
        base,
        metrics.asset,
        institutional_context,
        change_24h=change_24h,
        quote_volume=quote_volume,
        apply_hub=True,
    )
    return round(_clamp(adjusted), 2), breakdown, metrics


def calculate_opportunity_score(
    opportunity: Any,
    kind: OpportunityKind,
    institutional_context: dict[str, Any] | None = None,
) -> float:
    """
    Deterministic 0-100 score from net profit, liquidity depth, and stability,
    then unified multimodal adjustments (same stack as dashboard Oracle).
    """
    score, _breakdown, _metrics = score_opportunity_with_breakdown(
        opportunity, kind, institutional_context
    )
    return score


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

    try:
        from ml.drift_monitor import calibrate_confidence

        calibration = calibrate_confidence(confidence)
        if calibration.get("calibrated"):
            confidence = float(calibration["calibrated_hit_rate_percent"])
    except Exception:
        pass

    summary = (
        f"{metrics.asset} {kind.replace('_', ' ')} setup scores "
        f"{opportunity_score:.1f}/100 with {confidence:.1f}% confidence (rules engine)."
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
    """Score, explain, and oracle-wrap a single opportunity via unified stack."""
    from oracle_unified import finalize_unified_score

    score, breakdown, metrics = score_opportunity_with_breakdown(
        opportunity, kind, institutional_context
    )
    try:
        from technical_analysis import build_ta_bundle

        ta = await build_ta_bundle(metrics.asset)
        if ta.get("available"):
            score = round(_clamp(score + float(ta.get("score_adjustment") or 0)), 2)
    except Exception:
        logger.warning("TA bundle unavailable | asset=%s", metrics.asset)

    price_hint = 0.0
    if hasattr(opportunity, "model_dump"):
        raw_payload = opportunity.model_dump()
    elif isinstance(opportunity, dict):
        raw_payload = dict(opportunity)
    elif hasattr(opportunity, "__dict__"):
        raw_payload = {
            key: value
            for key, value in vars(opportunity).items()
            if not str(key).startswith("_")
        }
    else:
        raw_payload = {}
    for key in ("price", "spot_price", "mark_price", "buy_price", "mid_price"):
        try:
            value = float(raw_payload.get(key) or 0)
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            price_hint = value
            break

    finalized = await finalize_unified_score(
        score,
        metrics.asset,
        breakdown,
        price=price_hint,
        change_24h=float(raw_payload.get("change_24h") or 0.0),
        quote_volume=float(metrics.quote_amount or 0.0),
        include_ml=True,
    )
    score = float(finalized["opportunity_score"])

    # D3 Net-Edge Truth + D4 Half-Life — unique executable-edge gates
    from net_edge_truth import apply_truth_gate_to_score, compute_net_edge_truth
    from opportunity_tracker import estimate_opportunity_half_life, touch_opportunity
    from persona_clarity import build_persona_clarity

    truth_input = dict(raw_payload)
    truth_input.setdefault("kind", kind)
    truth_input.setdefault("asset", metrics.asset)
    truth_input["net_profit_usdt"] = metrics.net_profit_usdt
    truth_input["quote_amount"] = metrics.quote_amount
    truth_input["total_slippage_bps"] = metrics.total_slippage_bps
    truth = compute_net_edge_truth(truth_input)
    score = apply_truth_gate_to_score(score, truth)

    duration_meta = touch_opportunity(truth_input)
    half_life = estimate_opportunity_half_life(
        truth_input, live_duration_seconds=float(duration_meta.get("duration_seconds") or 0)
    )

    explanation = explain_opportunity(opportunity, kind, score, institutional_context)
    if truth.get("reject"):
        explanation.risk_factors = list(explanation.risk_factors) + [
            "Net-Edge Truth rejected: residual edge fails after latency/crowd/fees."
        ]
        explanation.reasons = list(explanation.reasons) + [
            f"Truth Score {truth.get('truth_score')}/100 — executable edge not proven."
        ]
    if half_life.get("remaining_seconds") is not None:
        explanation.reasons = list(explanation.reasons) + [
            f"Opportunity half-life ~{half_life.get('expected_half_life_seconds')}s; "
            f"~{half_life.get('remaining_seconds')}s remaining "
            f"(P(disappear)={half_life.get('disappearance_probability')})."
        ]

    # Prefer unified conflict-aware internal verdict; keep sentence generation.
    oracle = await get_single_sentence_oracle(
        explanation.asset, score, explanation, institutional_context
    )
    internal = str(finalized.get("internal_verdict") or oracle.verdict)
    if finalized.get("dimension_conflict", {}).get("veto") or finalized.get(
        "dimension_conflict", {}
    ).get("abstain"):
        internal = "Do Not Touch"
    if truth.get("reject"):
        internal = "Do Not Touch"
    oracle = OracleResponse(
        verdict=internal if internal in {"Buy Now", "Do Not Touch"} else oracle.verdict,
        sentence=inject_oracle_onchain_analytics(
            oracle.sentence,
            explanation.asset,
            institutional_context,
        ),
    )

    payload = dict(raw_payload)
    payload["unified_engine"] = finalized.get("engine")
    payload["public_verdict"] = finalized.get("verdict")
    payload["dimension_conflict"] = finalized.get("dimension_conflict")
    payload["market_regime"] = finalized.get("market_regime")
    payload["ml"] = finalized.get("ml")
    payload["net_edge_truth"] = truth
    payload["opportunity_half_life"] = half_life
    payload["persona_clarity"] = build_persona_clarity(
        asset=metrics.asset,
        score=score,
        verdict=oracle.verdict,
        payload=payload,
        net_profit_usdt=metrics.net_profit_usdt,
    )

    # D8 Sovereign Signal Registry — labeled lexicon row per decision
    try:
        from signal_registry import register_from_evaluation

        signal_row = register_from_evaluation(
            {
                "kind": kind,
                "asset": metrics.asset,
                "opportunity_score": score,
                "net_profit_usdt": metrics.net_profit_usdt,
                "oracle": {"verdict": oracle.verdict},
                "payload": payload,
            }
        )
        payload["signal_registry"] = {
            "signal_id": signal_row.get("signal_id"),
            "features_hash": signal_row.get("features_hash"),
            "label": signal_row.get("label"),
        }
    except Exception:
        logger.debug("signal registry write skipped", exc_info=True)

    try:
        from decision_certificate import compliance_footer_block

        payload["compliance_footer"] = compliance_footer_block(
            surface="ai_oracle_evaluate",
            trust_basis="public_accuracy_ledger + net_edge_truth + veto",
        )
    except Exception:
        pass

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
    try:
        from ml.labeling_pipeline import log_oracle_signal

        price_hint = await _resolve_training_price(evaluated.asset, evaluated.payload)
        public_verdict = str(
            evaluated.payload.get("public_verdict") or evaluated.oracle.verdict
        )
        await log_oracle_signal(
            asset=evaluated.asset,
            price=price_hint,
            verdict=public_verdict,
            opportunity_score=evaluated.opportunity_score,
            confidence=evaluated.explanation.confidence_percent,
            kind=evaluated.kind,
            source="arb_unified_v1",
            market_regime=str(
                (evaluated.payload or {}).get("market_regime")
                or ((evaluated.payload or {}).get("modal_breakdown") or {}).get("market_regime")
                or "neutral"
            ),
        )
    except Exception:
        logger.warning("Oracle prediction logging failed | asset=%s", evaluated.asset)
    try:
        from b2b_websocket_hub import publish_oracle_signal

        await publish_oracle_signal(
            {
                "asset": evaluated.asset,
                "kind": evaluated.kind,
                "engine": evaluated.payload.get("unified_engine") or "unified_multimodal_v1",
                "oracle_verdict": evaluated.oracle.verdict,
                "public_verdict": evaluated.payload.get("public_verdict"),
                "sentence": evaluated.oracle.sentence,
                "opportunity_score": evaluated.opportunity_score,
                "confidence_percent": evaluated.explanation.confidence_percent,
                "net_profit_usdt": evaluated.net_profit_usdt,
            }
        )
    except Exception:
        logger.debug("B2B oracle signal publish skipped | asset=%s", evaluated.asset)
    return evaluated


async def _resolve_training_price(asset: str, payload: dict[str, Any]) -> float:
    """Best-effort mid price so arb samples are not logged at price=0."""
    for key in ("price", "spot_price", "mark_price", "mid_price", "buy_price", "sell_price"):
        try:
            value = float(payload.get(key) or 0)
        except (TypeError, ValueError):
            value = 0.0
        if value > 0:
            return value
    try:
        buy = float(payload.get("buy_price") or payload.get("ask") or 0)
        sell = float(payload.get("sell_price") or payload.get("bid") or 0)
        if buy > 0 and sell > 0:
            return (buy + sell) / 2.0
    except (TypeError, ValueError):
        pass
    try:
        from live_book_hub import get_best_price

        for exchange in ("binance", "okx", "bybit"):
            quote = get_best_price(exchange, f"{asset}/USDT")
            if quote and quote.get("mid"):
                return float(quote["mid"])
    except Exception:
        logger.debug("Live book price lookup failed | asset=%s", asset, exc_info=True)
    try:
        from ml.labeling_pipeline import fetch_reference_price

        ref = await fetch_reference_price(asset)
        if ref and ref > 0:
            return float(ref)
    except Exception:
        logger.debug("Reference price lookup failed | asset=%s", asset, exc_info=True)
    return 0.0


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
