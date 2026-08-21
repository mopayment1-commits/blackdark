"""
BLACKDARK — Constitution decision enrichment for the primary Oracle path.

Attaches D3 Net-Edge Truth, D4 Half-Life, D7 Persona Clarity, D8 Signal Registry
to dashboard `/oracle/{symbol}` responses (not only the arb evaluate path).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.DecisionEnrichment")


def _truth_withdrawal_fee_usdt(out: dict[str, Any]) -> float | None:
    """Preserve unknown withdrawal as None — never invent 0.0 for Truth Score inputs."""
    if "withdrawal_fee_usdt" not in out:
        return None
    raw = out.get("withdrawal_fee_usdt")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _truth_input(out: dict[str, Any], asset: str, score: float, net_profit: float) -> dict[str, Any]:
    """Build Truth inputs without inventing optimistic slip/net when fields are absent.

    Directional oracle paths without explicit edge economics omit Truth fields so
    compute_net_edge_truth fail-closes rather than scoring synthetic 8bps / 0 fees.
    """
    payload: dict[str, Any] = {
        "kind": out.get("kind") or "oracle_direction",
        "asset": asset,
        "quote_age_ms": out.get("quote_age_ms"),
        "estimated_recipients": int(out.get("estimated_recipients") or 5),
    }
    if "quote_amount" in out and out.get("quote_amount") is not None:
        payload["quote_amount"] = float(out["quote_amount"])
    elif "volume_24h" in out and out.get("volume_24h") is not None:
        payload["quote_amount"] = float(out["volume_24h"])
    # Only pass net/slip/fees when present — never invent defaults for Truth.
    if net_profit and net_profit > 0:
        payload["net_profit_usdt"] = float(net_profit)
    elif "net_profit_usdt" in out and out.get("net_profit_usdt") is not None:
        payload["net_profit_usdt"] = float(out["net_profit_usdt"])
    if "total_slippage_bps" in out and out.get("total_slippage_bps") is not None:
        payload["total_slippage_bps"] = float(out["total_slippage_bps"])
    if "trading_fees_usdt" in out and out.get("trading_fees_usdt") is not None:
        payload["trading_fees_usdt"] = float(out["trading_fees_usdt"])
    elif "fees_usdt" in out and out.get("fees_usdt") is not None:
        payload["trading_fees_usdt"] = float(out["fees_usdt"])
    if "withdrawal_fee_usdt" in out:
        payload["withdrawal_fee_usdt"] = _truth_withdrawal_fee_usdt(out)
    return payload


def _has_explicit_edge(out: dict[str, Any], net_profit: float) -> bool:
    return out.get("kind") in {"cross_exchange", "triangular", "spot_futures", "funding"} or net_profit > 0


def _directional_truth_input(truth_input: dict[str, Any], score: float) -> dict[str, Any]:
    """Directional oracle: do not invent slip/fees/net for Truth — mark indicative only."""
    return {
        **truth_input,
        # Keep score for UI; Truth gate itself fail-closes without full economics.
        "oracle_score": score,
        "truth_indicative_only": True,
    }


def _apply_truth_reject(out: dict[str, Any], truth: dict[str, Any], verdict: str) -> str:
    if not truth.get("reject"):
        return verdict
    from regulatory_compliance_guard import to_public_verdict

    out["verdict"] = to_public_verdict("Do Not Touch")
    return out["verdict"]


def _attach_net_edge_truth(
    out: dict[str, Any],
    asset: str,
    score: float,
    verdict: str,
    net_profit: float,
) -> tuple[float, str]:
    try:
        from net_edge_truth import apply_truth_gate_to_score, compute_net_edge_truth

        truth_input = _truth_input(out, asset, score, net_profit)
        if _has_explicit_edge(out, net_profit):
            truth = compute_net_edge_truth(truth_input)
            score = apply_truth_gate_to_score(score, truth)
            out["opportunity_score"] = round(score)
            verdict = _apply_truth_reject(out, truth, verdict)
        else:
            truth = compute_net_edge_truth(_directional_truth_input(truth_input, score))
            truth = {
                **truth,
                "mode": "directional_advisory",
                "reject": False,
                "pass": True,
                "executable": False,
                "label": "ADVISORY_NOT_EXECUTABLE",
                "disclaimer": (
                    "Directional / advisory signal only — not an executable "
                    "profit claim. Fees, slip, and capacity are not fully proven."
                ),
            }
            out["truth_mode"] = "advisory"
            out["executable"] = False
        out["net_edge_truth"] = truth
    except Exception:
        logger.debug("net edge enrich failed", exc_info=True)
        out["net_edge_truth"] = {"enabled": False, "error": "unavailable"}
    return score, verdict


def _calibrated_directional_half_life(half: dict[str, Any], meta: dict[str, Any], samples: int) -> dict[str, Any]:
    lived = float(meta.get("duration_seconds") or 0)
    prior = 3600.0
    weight = min(1.0, samples / 20.0)
    blended = prior * (1 - weight) + float(half.get("expected_half_life_seconds") or prior) * weight
    return {
        **half,
        "expected_half_life_seconds": round(blended, 2),
        "remaining_seconds": max(0.0, blended - lived),
        "model": "directional_horizon_calibrated_v2",
        "urgency": "normal",
        "cold_start": False,
        "calibrated_prior": True,
        "history_samples": samples,
        "note": "Calibrated 1h directional prior blended with observed half-life history",
    }


def _attach_half_life(out: dict[str, Any], asset: str) -> None:
    try:
        from opportunity_tracker import (
            estimate_opportunity_half_life,
            half_life_sample_count,
            seed_directional_half_life_priors,
            touch_opportunity,
        )

        if half_life_sample_count("oracle_direction") < 3:
            seed_directional_half_life_priors(n=12)
        meta = touch_opportunity({"kind": "oracle_direction", "asset": asset})
        half = estimate_opportunity_half_life(
            {"kind": "oracle_direction", "asset": asset},
            live_duration_seconds=float(meta.get("duration_seconds") or 0),
        )
        samples = half_life_sample_count("oracle_direction", asset)
        if half.get("expected_half_life_seconds", 0) < 30 or samples < 3:
            half = _calibrated_directional_half_life(half, meta, samples)
        out["opportunity_half_life"] = half
    except Exception:
        logger.debug("half-life enrich failed", exc_info=True)
        out["opportunity_half_life"] = {"error": "unavailable"}


def _ensure_dimension_conflict(out: dict[str, Any]) -> None:
    if isinstance(out.get("dimension_conflict"), dict):
        return
    modal = out.get("modal_breakdown") or {}
    conflicts = modal.get("conflicts") if isinstance(modal, dict) else None
    if isinstance(conflicts, dict):
        out["dimension_conflict"] = conflicts


def _attach_persona(out: dict[str, Any], asset: str, score: float, verdict: str, net_profit: float) -> None:
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


def _register_signal(out: dict[str, Any], asset: str, verdict: str, net_profit: float) -> None:
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


def _apply_ux_mode(out: dict[str, Any], ux_mode: str, lang: str) -> dict[str, Any]:
    try:
        from ux_mode import apply_ux_mode

        return apply_ux_mode(out, mode=ux_mode, lang=lang)
    except Exception:
        logger.debug("ux mode filter failed", exc_info=True)
        out["ux_mode"] = ux_mode
        out["lang"] = lang
        return out


def _constitution_block() -> dict[str, Any]:
    return {
        "ref": "docs/PRODUCT_CONSTITUTION_AR.md",
        "capabilities": [
            "Unified Financial Oracle",
            "Net-Edge & Risk Gate",
            "Public Accuracy & Audit Chain",
            "Labeled Data Flywheel",
        ],
        "differentiators": ["D1", "D2", "D3", "D4", "D5", "D7", "D8"],
    }


def _record_platform_compounding(
    out: dict[str, Any],
    asset: str,
    verdict: str,
    *,
    user_id: str | None = None,
    tier: str | None = None,
    surface: str = "oracle",
) -> None:
    try:
        from cap646.evidence_class import infer_evidence_class
        from decision_certificate import build_decision_certificate
        from decision_ledger import link_exposure, record_decision
        from user_exposure_log import record_user_exposure

        prediction_id = str(
            out.get("prediction_id")
            or (out.get("signal_registry") or {}).get("signal_id")
            or f"oracle_{asset.lower()}"
        )
        evidence_class = infer_evidence_class(source=str(out.get("source") or "oracle"))
        cert = build_decision_certificate(
            {
                **out,
                "symbol": asset,
                "prediction_id": prediction_id,
                "decision_action": out.get("decision_action") or verdict,
                "tier": tier or out.get("tier") or "pro",
            }
        )
        decision = record_decision(
            prediction_id=prediction_id,
            decision_action=str(out.get("decision_action") or verdict),
            symbol=asset,
            certificate_hash=cert.get("certificate_hash"),
            evidence_class=evidence_class,
            source="oracle_enrichment",
            meta={"surface": surface},
        )
        exposure = record_user_exposure(
            user_id=user_id or "anonymous",
            tier=str(tier or out.get("tier") or "free"),
            surface=surface,
            decision_id=decision.get("decision_id"),
            prediction_id=prediction_id,
            symbol=asset,
            evidence_class=evidence_class,
            source="oracle_enrichment",
        )
        if decision.get("decision_id") and exposure.get("exposure_id"):
            link_exposure(str(decision["decision_id"]), str(exposure["exposure_id"]))
        out["platform_compounding"] = {
            "decision_id": decision.get("decision_id"),
            "exposure_id": exposure.get("exposure_id"),
            "certificate_hash": cert.get("certificate_hash"),
        }
    except Exception:
        logger.debug("platform compounding record failed", exc_info=True)


def enrich_oracle_decision(
    payload: dict[str, Any],
    *,
    ux_mode: str = "beginner",
    lang: str = "en",
    register_signal: bool = True,
    user_id: str | None = None,
    tier: str | None = None,
    surface: str = "oracle",
) -> dict[str, Any]:
    """Mutate/return oracle payload with constitution differentiators."""
    out = dict(payload)
    asset = str(out.get("symbol") or out.get("asset") or "BTC").upper()
    score = float(out.get("opportunity_score") or 0)
    verdict = str(out.get("verdict") or "WAIT")
    net_profit = float(out.get("net_profit_usdt") or 0.0)

    score, verdict = _attach_net_edge_truth(out, asset, score, verdict, net_profit)
    _attach_half_life(out, asset)
    # Ensure contradiction meta is visible to persona + registry before labeling.
    _ensure_dimension_conflict(out)
    _attach_persona(out, asset, score, verdict, net_profit)

    if register_signal:
        _register_signal(out, asset, verdict, net_profit)

    _record_platform_compounding(out, asset, verdict, user_id=user_id, tier=tier, surface=surface)

    out = _apply_ux_mode(out, ux_mode, lang)
    out["constitution"] = _constitution_block()
    return out
