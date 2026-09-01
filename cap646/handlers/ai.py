"""AI, oracle, decision capabilities."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import ai_compliance_footer


async def handle_ai_capability(capability_id: int, *, params: dict[str, Any]) -> dict[str, Any]:
    symbol = str(params.get("symbol") or params.get("asset") or "BTC").upper().replace("/USDT", "")

    if capability_id == 642:
        from decision_certificate import build_decision_certificate

        cert = build_decision_certificate(
            {
                "symbol": symbol,
                "prediction_id": params.get("prediction_id") or "ai-provenance",
                "decision_action": "WAIT",
                "decision_sentence": "AI output carries compliance footer and evidence class.",
                "tier": params.get("tier") or "pro",
            }
        )
        return ai_compliance_footer(
            {
                "capability_id": 642,
                "surface": "ai_output_provenance_compliance_footer",
                "certificate": cert,
                "provenance": cert,
                "success": True,
            }
        )

    verified = {638, 640, 641, 639}
    if capability_id in verified:
        from cap646.handlers.verified import handle_verified_capability

        return await handle_verified_capability(capability_id, params=params)

    if capability_id in {591, 592, 129, 175}:
        from sentiment_engine import build_sentiment_context_safe
        from sentiment_gate import fetch_asset_sentiment

        ctx = await build_sentiment_context_safe(symbol)
        gate = await fetch_asset_sentiment(symbol)
        return ai_compliance_footer(
            {"capability_id": capability_id, "surface": "sentiment_ai", "context": ctx, "gate": gate, "success": True}
        )

    if capability_id == 53:
        from macro_correlations import build_macro_context_safe
        from market_context import fetch_binance_ticker

        macro = await build_macro_context_safe()
        ticker = await fetch_binance_ticker(f"{symbol}USDT")
        change_24h = float((ticker or {}).get("change_24h") or 0)
        coupling = {
            "btc_symbol": symbol,
            "btc_change_24h_pct": change_24h,
            "macro_regime": macro.get("macro_regime"),
            "dxy_score": macro.get("dxy_score"),
            "spx_score": macro.get("spx_score"),
            "btc_gold_ratio": macro.get("btc_gold_ratio"),
            "btc_gold_score": macro.get("btc_gold_score"),
            "coupling_read": (
                "risk_on_aligned"
                if macro.get("macro_regime") == "Risk-On" and change_24h > 0
                else "risk_off_divergence"
                if macro.get("macro_regime") == "Risk-Off" and change_24h > 0
                else "neutral_coupling"
            ),
        }
        return ai_compliance_footer(
            {
                "capability_id": 53,
                "surface": "btc_to_macro_coupling",
                "btc_to_macro_coupling": coupling,
                "macro_context": macro,
                "success": bool(macro),
            }
        )

    try:
        from ai_oracle import OpportunityKind, evaluate_opportunity

        opp = params.get("opportunity") or {"asset": symbol, "symbol": f"{symbol}/USDT"}
        kind: OpportunityKind = str(params.get("kind") or "spot_futures")  # type: ignore[assignment]
        result = await evaluate_opportunity(opp, kind)
        return ai_compliance_footer(
            {"capability_id": capability_id, "surface": "ai_decision_intelligence", "result": result, "success": bool(result)}
        )
    except Exception as exc:
        from trust_pulse import build_trust_pulse

        pulse = await build_trust_pulse(symbol) if hasattr(__import__("trust_pulse"), "build_trust_pulse") else {}
        return ai_compliance_footer(
            {
                "capability_id": capability_id,
                "surface": "ai_decision_intelligence",
                "trust_pulse": pulse,
                "oracle_fallback_error": str(exc),
                "success": bool(pulse),
            }
        )
