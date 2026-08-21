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
            {"capability_id": 642, "surface": "ai_output_provenance_compliance_footer", "certificate": cert, "success": True}
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

    try:
        from ai_oracle import evaluate_opportunity

        opp = params.get("opportunity") or {"asset": symbol, "symbol": f"{symbol}/USDT"}
        result = await evaluate_opportunity(opp)
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
