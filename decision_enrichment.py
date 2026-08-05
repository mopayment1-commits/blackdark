"""
BLACKDARK — Constitution decision enrichment for the primary Oracle path.

Attaches D3 Net-Edge Truth, D4 Half-Life, D7 Persona Clarity, D8 Signal Registry
to dashboard `/oracle/{symbol}` responses (not only the arb evaluate path).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.DecisionEnrichment")


def enrich_oracle_decision(
    payload: dict[str, Any],
    *,
    ux_mode: str = "beginner",
    lang: str = "en",
    register_signal: bool = True,
) -> dict[str, Any]:
    """Mutate/return oracle payload with constitution differentiators."""
    out = dict(payload)
    asset = str(out.get("symbol") or out.get("asset") or "BTC").upper()
    score = float(out.get("opportunity_score") or 0)
    verdict = str(out.get("verdict") or "WAIT")
    net_profit = float(out.get("net_profit_usdt") or 0.0)

    # Synthetic edge proxy for directional oracle (non-arb): use score as confidence of edge
    truth_input = {
        "kind": out.get("kind") or "oracle_direction",
        "asset": asset,
        "net_profit_usdt": net_profit if net_profit else max(0.0, (score - 50.0) / 50.0),
        "quote_amount": float(out.get("quote_amount") or out.get("volume_24h") or 1000),
        "total_slippage_bps": float(out.get("total_slippage_bps") or 8.0),
        "withdrawal_fee_usdt": float(out.get("withdrawal_fee_usdt") or 0.0),
        "quote_age_ms": out.get("quote_age_ms"),
        "estimated_recipients": int(out.get("estimated_recipients") or 5),
    }

    try:
        from net_edge_truth import apply_truth_gate_to_score, compute_net_edge_truth

        # Directional oracle: Truth is advisory unless explicit arb economics present
        if out.get("kind") in {"cross_exchange", "triangular", "spot_futures", "funding"} or net_profit > 0:
            truth = compute_net_edge_truth(truth_input)
            score = apply_truth_gate_to_score(score, truth)
            out["opportunity_score"] = int(round(score))
            if truth.get("reject"):
                from regulatory_compliance_guard import to_public_verdict

                out["verdict"] = to_public_verdict("Do Not Touch")
                verdict = out["verdict"]
        else:
            # Soft truth for directional: still expose score for pros without hard kill
            truth = compute_net_edge_truth(
                {
                    **truth_input,
                    "net_profit_usdt": max(0.15, (score / 100.0) * 0.5),
                    "quote_age_ms": truth_input.get("quote_age_ms") or 300,
                    "total_slippage_bps": 5.0,
                }
            )
            truth = {**truth, "mode": "directional_advisory", "reject": False, "pass": True}
        out["net_edge_truth"] = truth
    except Exception:
        logger.debug("net edge enrich failed", exc_info=True)
        out["net_edge_truth"] = {"enabled": False, "error": "unavailable"}

    try:
        from opportunity_tracker import estimate_opportunity_half_life, touch_opportunity

        meta = touch_opportunity({"kind": "oracle_direction", "asset": asset})
        half = estimate_opportunity_half_life(
            {"kind": "oracle_direction", "asset": asset},
            live_duration_seconds=float(meta.get("duration_seconds") or 0),
        )
        # Directional decisions use longer horizon default if history thin
        if half.get("expected_half_life_seconds", 0) < 30:
            half = {
                **half,
                "expected_half_life_seconds": 3600,
                "remaining_seconds": max(0, 3600 - float(meta.get("duration_seconds") or 0)),
                "model": "directional_horizon_1h_v1",
                "urgency": "normal",
            }
        out["opportunity_half_life"] = half
    except Exception:
        logger.debug("half-life enrich failed", exc_info=True)
        out["opportunity_half_life"] = {"error": "unavailable"}

    # Ensure contradiction meta is visible to persona + registry before labeling.
    if not isinstance(out.get("dimension_conflict"), dict):
        modal = out.get("modal_breakdown") or {}
        conflicts = modal.get("conflicts") if isinstance(modal, dict) else None
        if isinstance(conflicts, dict):
            out["dimension_conflict"] = conflicts

    try:
        from persona_clarity import build_persona_clarity

        persona = build_persona_clarity(
            asset=asset,
            score=float(out.get("opportunity_score") or score),
            verdict=verdict,
            payload=out,
            net_profit_usdt=net_profit,
        )
        out["persona_clarity"] = persona
        # Site is English-only; always prefer EN decision sentence for UI.
        retail = (persona.get("personas") or {}).get("retail") or {}
        out["decision_sentence"] = retail.get("en") or retail.get("text") or out.get("oracle")
        out["decision_action"] = persona.get("action")
    except Exception:
        logger.debug("persona enrich failed", exc_info=True)

    if register_signal:
        try:
            from signal_registry import register_from_evaluation

            row = register_from_evaluation(
                {
                    "kind": out.get("kind") or "oracle_direction",
                    "asset": asset,
                    "opportunity_score": out.get("opportunity_score"),
                    "net_profit_usdt": net_profit,
                    "oracle": {"verdict": verdict},
                    "payload": out,
                }
            )
            out["signal_registry"] = {
                "signal_id": row.get("signal_id"),
                "features_hash": row.get("features_hash"),
                "label": row.get("label"),
            }
            # D1 proof id must come from audit/log_oracle_signal — never overwrite a real id.
            if out.get("prediction_id") in (None, "", 0):
                out["prediction_id_fallback"] = row.get("signal_id")
        except Exception:
            logger.debug("signal registry enrich failed", exc_info=True)

    try:
        from ux_mode import apply_ux_mode

        out = apply_ux_mode(out, mode=ux_mode, lang=lang)
    except Exception:
        logger.debug("ux mode filter failed", exc_info=True)
        out["ux_mode"] = ux_mode
        out["lang"] = lang

    out["constitution"] = {
        "ref": "docs/PRODUCT_CONSTITUTION_AR.md",
        "capabilities": [
            "Unified Financial Oracle",
            "Net-Edge & Risk Gate",
            "Public Accuracy & Audit Chain",
            "Labeled Data Flywheel",
        ],
        "differentiators": ["D1", "D2", "D3", "D4", "D5", "D7", "D8"],
    }
    return out
